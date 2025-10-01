"""
Matching services for ReferWell Direct.
"""
import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.calibration import CalibratedClassifierCV

# Lazy import - will be imported when needed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

from django.conf import settings
from django.contrib.gis.db.models import Q
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models import F, QuerySet

from catalogue.models import Psychologist
from referrals.models import Referral

logger = logging.getLogger(__name__)


class ProbabilityCalibrationService:
    """
    Service for calibrating matching probabilities using isotonic regression or Platt scaling.
    """

    def __init__(self, calibration_type: str = "isotonic"):
        """
        Initialize calibration service.

        Args:
            calibration_type: Type of calibration ('isotonic' or 'platt')
        """
        self.calibration_type = calibration_type
        self.calibrator = None
        self.is_fitted = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def fit(self, scores: np.ndarray, labels: np.ndarray) -> bool:
        """
        Fit the calibration model.

        Args:
            scores: Raw matching scores (0-1)
            labels: Binary labels (1 for good match, 0 for bad match)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.calibration_type == "isotonic":
                self.calibrator = IsotonicRegression(out_of_bounds="clip")
            elif self.calibration_type == "platt":
                # Use logistic regression for Platt scaling
                self.calibrator = LogisticRegression()
            else:
                raise ValueError(f"Unknown calibration type: {self.calibration_type}")

            # Fit the calibrator
            self.calibrator.fit(scores.reshape(-1, 1), labels)
            self.is_fitted = True

            self.logger.info(f"Fitted {self.calibration_type} calibration model")
            return True

        except Exception as e:
            self.logger.error(f"Failed to fit calibration model: {e}")
            return False

    def calibrate_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Calibrate raw scores to probabilities.

        Args:
            scores: Raw matching scores to calibrate

        Returns:
            Calibrated probabilities
        """
        if not self.is_fitted:
            self.logger.warning("Calibration model not fitted, returning raw scores")
            return scores

        try:
            if self.calibration_type == "isotonic":
                calibrated = self.calibrator.transform(scores.reshape(-1, 1)).flatten()
            else:  # platt
                calibrated = self.calibrator.predict_proba(scores.reshape(-1, 1))[:, 1]

            # Ensure probabilities are in [0, 1] range
            calibrated = np.clip(calibrated, 0.0, 1.0)

            return calibrated

        except Exception as e:
            self.logger.error(f"Failed to calibrate scores: {e}")
            return scores

    def calibrate_single_score(self, score: float) -> float:
        """
        Calibrate a single score.

        Args:
            score: Raw matching score to calibrate

        Returns:
            Calibrated probability
        """
        calibrated = self.calibrate_scores(np.array([score]))
        return float(calibrated[0])

    def get_calibration_metrics(
        self, scores: np.ndarray, labels: np.ndarray
    ) -> dict[str, float]:
        """
        Calculate calibration metrics.

        Args:
            scores: Raw matching scores
            labels: Binary labels

        Returns:
            Dictionary of calibration metrics
        """
        if not self.is_fitted:
            return {}

        try:
            from sklearn.metrics import brier_score_loss, log_loss

            calibrated_scores = self.calibrate_scores(scores)

            brier_score = brier_score_loss(labels, calibrated_scores)
            log_loss_score = log_loss(labels, calibrated_scores)

            # Calculate reliability (calibration error)
            n_bins = 10
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]

            ece = 0  # Expected Calibration Error
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = (calibrated_scores > bin_lower) & (
                    calibrated_scores <= bin_upper
                )
                prop_in_bin = in_bin.mean()

                if prop_in_bin > 0:
                    accuracy_in_bin = labels[in_bin].mean()
                    avg_confidence_in_bin = calibrated_scores[in_bin].mean()
                    ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

            return {
                "brier_score": brier_score,
                "log_loss": log_loss_score,
                "expected_calibration_error": ece,
                "calibration_type": self.calibration_type,
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate calibration metrics: {e}")
            return {}

    def save_model(self, filepath: str) -> bool:
        """
        Save the calibration model to disk.

        Args:
            filepath: Path to save the model

        Returns:
            True if successful, False otherwise
        """
        if not self.is_fitted:
            self.logger.warning("No fitted model to save")
            return False

        try:
            with open(filepath, "wb") as f:
                pickle.dump(
                    {
                        "calibrator": self.calibrator,
                        "calibration_type": self.calibration_type,
                        "is_fitted": self.is_fitted,
                    },
                    f,
                )

            self.logger.info(f"Saved calibration model to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save calibration model: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """
        Load a calibration model from disk.

        Args:
            filepath: Path to load the model from

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)

            self.calibrator = model_data["calibrator"]
            self.calibration_type = model_data["calibration_type"]
            self.is_fitted = model_data["is_fitted"]

            self.logger.info(f"Loaded calibration model from {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load calibration model: {e}")
            return False


class VectorEmbeddingService:
    """
    Service for generating and managing vector embeddings using Sentence-Transformers.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_timeout: int = 3600):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the Sentence-Transformers model to use
            cache_timeout: Cache timeout in seconds (default: 1 hour)
        """
        self.model_name = model_name
        self.model = None
        self.cache_timeout = cache_timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Don't load model on initialization - load lazily when needed

    def _load_model(self):
        """Load the Sentence-Transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text with caching.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            self._load_model()

        # Check cache first
        cache_key = f"embedding_{self.model_name}_{hash(text)}"
        cached_embedding = cache.get(cache_key)

        if cached_embedding is not None:
            self.logger.debug(f"Cache hit for embedding: {cache_key}")
            return cached_embedding

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)

            # Cache the embedding
            cache.set(cache_key, embedding, self.cache_timeout)
            self.logger.debug(f"Cached embedding: {cache_key}")

            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts with caching.

        Args:
            texts: List of texts to embed

        Returns:
            Array of embedding vectors
        """
        if not self.model:
            self._load_model()

        # Check cache for each text
        embeddings = []
        texts_to_process = []
        text_indices = []

        for i, text in enumerate(texts):
            cache_key = f"embedding_{self.model_name}_{hash(text)}"
            cached_embedding = cache.get(cache_key)

            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                texts_to_process.append(text)
                text_indices.append(i)
                embeddings.append(None)  # Placeholder

        # Process uncached texts
        if texts_to_process:
            try:
                new_embeddings = self.model.encode(
                    texts_to_process, convert_to_numpy=True
                )

                # Cache new embeddings and update results
                for i, (text, embedding) in enumerate(
                    zip(texts_to_process, new_embeddings)
                ):
                    cache_key = f"embedding_{self.model_name}_{hash(text)}"
                    cache.set(cache_key, embedding, self.cache_timeout)
                    embeddings[text_indices[i]] = embedding

            except Exception as e:
                self.logger.error(f"Failed to generate batch embeddings: {e}")
                raise

        return np.array(embeddings)

    def calculate_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            similarity = cosine_similarity([embedding1], [embedding2])[0][0]
            return float(similarity)
        except Exception as e:
            self.logger.error(f"Failed to calculate similarity: {e}")
            raise

    def update_psychologist_embedding(self, psychologist: Psychologist) -> bool:
        """
        Update embedding for a psychologist.

        Args:
            psychologist: Psychologist instance to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create text representation of psychologist
            text_parts = []

            # Add basic info
            if psychologist.user.first_name:
                text_parts.append(psychologist.user.first_name)
            if psychologist.user.last_name:
                text_parts.append(psychologist.user.last_name)

            # Add specialisms
            if psychologist.specialisms:
                text_parts.extend(psychologist.specialisms)

            # Add qualifications
            if psychologist.qualifications:
                text_parts.extend(psychologist.qualifications)

            # Add preferred conditions
            if psychologist.preferred_conditions:
                text_parts.extend(psychologist.preferred_conditions)

            # Join all text parts
            text = " ".join(text_parts)

            if not text.strip():
                self.logger.warning(
                    f"No text content for psychologist {psychologist.id}"
                )
                return False

            # Generate embedding
            embedding = self.generate_embedding(text)

            # Update psychologist
            psychologist.update_embedding(embedding)

            self.logger.info(f"Updated embedding for psychologist {psychologist.id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to update embedding for psychologist {psychologist.id}: {e}"
            )
            return False


class BM25Service:
    """
    Service for BM25-based lexical search.
    """

    def __init__(self, cache_timeout: int = 1800):
        self.vectorizer = None
        self.document_vectors = None
        self.document_ids = []
        self.cache_timeout = cache_timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def build_index(self, psychologists: QuerySet[Psychologist]) -> bool:
        """
        Build BM25 index from psychologists.

        Args:
            psychologists: QuerySet of psychologists to index

        Returns:
            True if successful, False otherwise
        """
        try:
            documents = []
            self.document_ids = []

            for psychologist in psychologists:
                # Create text representation
                text_parts = []

                if psychologist.user.first_name:
                    text_parts.append(psychologist.user.first_name)
                if psychologist.user.last_name:
                    text_parts.append(psychologist.user.last_name)

                if psychologist.specialisms:
                    text_parts.extend(psychologist.specialisms)

                if psychologist.qualifications:
                    text_parts.extend(psychologist.qualifications)

                if psychologist.preferred_conditions:
                    text_parts.extend(psychologist.preferred_conditions)

                text = " ".join(text_parts)
                if text.strip():
                    documents.append(text)
                    self.document_ids.append(psychologist.id)

            if not documents:
                self.logger.warning("No documents to index")
                return False

            # Build TF-IDF vectors
            # Adjust parameters for small datasets
            min_df = max(1, len(documents) // 10) if len(documents) > 1 else 1
            max_df = (
                min(0.95, max(0.5, 1 - (1 / len(documents))))
                if len(documents) > 1
                else 0.95
            )

            self.vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=min_df,
                max_df=max_df,
            )

            self.document_vectors = self.vectorizer.fit_transform(documents)

            self.logger.info(f"Built BM25 index with {len(documents)} documents")
            return True

        except Exception as e:
            self.logger.error(f"Failed to build BM25 index: {e}")
            return False

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Search using BM25 with caching.

        Args:
            query: Search query
            top_k: Number of top results to return

        Returns:
            List of (psychologist_id, score) tuples
        """
        if not self.vectorizer or self.document_vectors is None:
            self.logger.warning("BM25 index not built")
            return []

        # Check cache first
        cache_key = f"bm25_search_{hash(query)}_{top_k}_{len(self.document_ids)}"
        cached_results = cache.get(cache_key)

        if cached_results is not None:
            self.logger.debug(f"Cache hit for BM25 search: {cache_key}")
            return cached_results

        try:
            # Transform query
            query_vector = self.vectorizer.transform([query])

            # Calculate similarities
            similarities = cosine_similarity(
                query_vector, self.document_vectors
            ).flatten()

            # Get top-k results
            top_indices = similarities.argsort()[-top_k:][::-1]

            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    psychologist_id = self.document_ids[idx]
                    score = float(similarities[idx])
                    results.append((psychologist_id, score))

            # Cache the results
            cache.set(cache_key, results, self.cache_timeout)
            self.logger.debug(f"Cached BM25 search results: {cache_key}")

            return results

        except Exception as e:
            self.logger.error(f"BM25 search failed: {e}")
            return []


class HybridRetrievalService:
    """
    Service that combines vector similarity and BM25 for hybrid retrieval.
    """

    def __init__(self, vector_weight: float = 0.7, bm25_weight: float = 0.3):
        """
        Initialize hybrid retrieval service.

        Args:
            vector_weight: Weight for vector similarity (0-1)
            bm25_weight: Weight for BM25 score (0-1)
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.vector_service = VectorEmbeddingService()
        self.bm25_service = BM25Service()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def search(
        self, query: str, psychologists: QuerySet[Psychologist], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search combining vector and BM25.

        Args:
            query: Search query
            psychologists: QuerySet of psychologists to search
            top_k: Number of results to return

        Returns:
            List of match dictionaries
        """
        try:
            # Build BM25 index
            if not self.bm25_service.build_index(psychologists):
                self.logger.warning(
                    "Failed to build BM25 index, falling back to vector only"
                )
                return self._vector_only_search(query, psychologists, top_k)

            # Get BM25 results
            bm25_results = self.bm25_service.search(
                query, top_k * 2
            )  # Get more for better coverage
            bm25_scores = {psych_id: score for psych_id, score in bm25_results}

            # Get vector results
            query_embedding = self.vector_service.generate_embedding(query)

            # Calculate vector similarities
            vector_results = []
            for psychologist in psychologists:
                if psychologist.embedding:
                    try:
                        psych_embedding = psychologist.get_embedding()
                        if psych_embedding is not None:
                            similarity = self.vector_service.calculate_similarity(
                                query_embedding, psych_embedding
                            )
                            vector_results.append((psychologist.id, similarity))
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to get embedding for psychologist {psychologist.id}: {e}"
                        )
                        continue

            # Sort vector results by similarity
            vector_results.sort(key=lambda x: x[1], reverse=True)
            vector_scores = {psych_id: score for psych_id, score in vector_results}

            # Combine scores
            combined_scores = {}
            all_psych_ids = set(bm25_scores.keys()) | set(vector_scores.keys())

            for psych_id in all_psych_ids:
                bm25_score = bm25_scores.get(psych_id, 0.0)
                vector_score = vector_scores.get(psych_id, 0.0)

                # Normalize scores to 0-1 range
                combined_score = (
                    self.vector_weight * vector_score + self.bm25_weight * bm25_score
                )
                combined_scores[psych_id] = combined_score

            # Sort by combined score
            sorted_results = sorted(
                combined_scores.items(), key=lambda x: x[1], reverse=True
            )

            # Get top-k results
            top_results = sorted_results[:top_k]

            # Build result dictionaries
            results = []
            for psych_id, score in top_results:
                try:
                    psychologist = psychologists.get(id=psych_id)
                    result = {
                        "psychologist": psychologist,
                        "score": score,
                        "vector_score": vector_scores.get(psych_id, 0.0),
                        "bm25_score": bm25_scores.get(psych_id, 0.0),
                        "explanation": {
                            "hybrid_search": True,
                            "vector_weight": self.vector_weight,
                            "bm25_weight": self.bm25_weight,
                        },
                    }
                    results.append(result)
                except Psychologist.DoesNotExist:
                    self.logger.warning(
                        f"Psychologist {psych_id} not found in queryset"
                    )
                    continue

            self.logger.info(f"Hybrid search returned {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Hybrid search failed: {e}")
            return []

    def _vector_only_search(
        self, query: str, psychologists: QuerySet[Psychologist], top_k: int
    ) -> list[dict[str, Any]]:
        """Fallback to vector-only search if BM25 fails."""
        try:
            query_embedding = self.vector_service.generate_embedding(query)

            results = []
            for psychologist in psychologists:
                if psychologist.embedding:
                    try:
                        psych_embedding = psychologist.get_embedding()
                        if psych_embedding is not None:
                            similarity = self.vector_service.calculate_similarity(
                                query_embedding, psych_embedding
                            )
                            results.append(
                                {
                                    "psychologist": psychologist,
                                    "score": similarity,
                                    "vector_score": similarity,
                                    "bm25_score": 0.0,
                                    "explanation": {
                                        "hybrid_search": False,
                                        "vector_only": True,
                                    },
                                }
                            )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to get embedding for psychologist {psychologist.id}: {e}"
                        )
                        continue

            # Sort by score and return top-k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            self.logger.error(f"Vector-only search failed: {e}")
            return []


class FeasibilityFilter:
    """
    Feasibility filter for psychologist matching.

    This filter applies basic criteria to narrow down the pool of psychologists
    before more expensive operations like vector similarity search.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def filter_psychologists(
        self, referral: Referral, psychologists: QuerySet[Psychologist] | None = None
    ) -> QuerySet[Psychologist]:
        """
        Filter psychologists based on feasibility criteria.

        Args:
            referral: The referral to match against
            psychologists: Optional queryset to filter (defaults to all active psychologists)

        Returns:
            Filtered queryset of psychologists
        """
        if psychologists is None:
            psychologists = Psychologist.objects.filter(
                is_active=True, is_accepting_referrals=True
            ).select_related("user")

        self.logger.info(f"Starting feasibility filter for referral {referral.id}")
        initial_count = psychologists.count()

        # Apply filters in order of selectivity (most selective first)
        psychologists = self._filter_by_service_type(psychologists, referral)
        psychologists = self._filter_by_modality(psychologists, referral)
        psychologists = self._filter_by_availability(psychologists, referral)
        psychologists = self._filter_by_radius(psychologists, referral)
        psychologists = self._filter_by_capacity(psychologists, referral)

        final_count = psychologists.count()
        self.logger.info(
            f"Feasibility filter complete: {initial_count} -> {final_count} psychologists"
        )

        return psychologists

    def _filter_by_service_type(
        self, psychologists: QuerySet[Psychologist], referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by NHS/private service type preference."""
        if not referral.service_type:
            return psychologists

        if referral.service_type == "nhs":
            return psychologists.filter(service_type__in=["nhs", "mixed"])
        elif referral.service_type == "private":
            return psychologists.filter(service_type__in=["private", "mixed"])
        elif referral.service_type == "mixed":
            return psychologists  # Mixed accepts all

        return psychologists

    def _filter_by_modality(
        self, psychologists: QuerySet[Psychologist], referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by remote vs in-person modality preference."""
        if not referral.modality:
            return psychologists

        if referral.modality == "remote":
            return psychologists.filter(modality__in=["remote", "mixed"])
        elif referral.modality == "in_person":
            return psychologists.filter(modality__in=["in_person", "mixed"])
        elif referral.modality == "mixed":
            return psychologists  # Mixed accepts all

        return psychologists

    def _filter_by_availability(
        self, psychologists: QuerySet[Psychologist], referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by availability status."""
        return psychologists.filter(
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE
        )

    def _filter_by_radius(
        self, psychologists: QuerySet[Psychologist], referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by geographic radius using PostGIS."""
        if not referral.preferred_latitude or not referral.preferred_longitude:
            self.logger.warning("No patient location provided for radius filtering")
            return psychologists

        if not referral.max_distance_km:
            self.logger.warning("No max distance specified for radius filtering")
            return psychologists

        # Convert km to meters
        max_distance_meters = referral.max_distance_km * 1000

        # Create point from patient location
        patient_point = Point(
            referral.preferred_longitude, referral.preferred_latitude, srid=4326
        )

        # Filter using PostGIS ST_DWithin for efficient radius queries
        # Only filter by radius if the psychologist has a location set
        return psychologists.filter(
            Q(location__isnull=True)
            | Q(location__dwithin=(patient_point, max_distance_meters))
        )

    def _filter_by_capacity(
        self, psychologists: QuerySet[Psychologist], referral: Referral
    ) -> QuerySet[Psychologist]:
        """Filter by psychologist capacity."""
        return psychologists.filter(current_patients__lt=F("max_patients"))


class MatchingService:
    """
    Main matching service that orchestrates the matching process.
    """

    def __init__(
        self,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        use_calibration: bool = True,
    ):
        """
        Initialize matching service.

        Args:
            vector_weight: Weight for vector similarity in hybrid search
            bm25_weight: Weight for BM25 score in hybrid search
            use_calibration: Whether to use probability calibration
        """
        self.feasibility_filter = FeasibilityFilter()
        self.hybrid_retrieval = HybridRetrievalService(vector_weight, bm25_weight)
        self.vector_service = VectorEmbeddingService()
        self.calibration_service = (
            ProbabilityCalibrationService() if use_calibration else None
        )
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def find_matches(
        self, referral: Referral, limit: int = 10, use_hybrid: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Find matching psychologists for a referral.

        Args:
            referral: The referral to match
            limit: Maximum number of matches to return
            use_hybrid: Whether to use hybrid retrieval (vector + BM25)

        Returns:
            List of match dictionaries with psychologist and score
        """
        self.logger.info(f"Starting matching process for referral {referral.id}")

        # Step 1: Apply feasibility filter
        feasible_psychologists = self.feasibility_filter.filter_psychologists(referral)

        if not feasible_psychologists.exists():
            self.logger.warning(
                f"No feasible psychologists found for referral {referral.id}"
            )
            return []

        # Step 2: Create search query from referral
        query = self._create_search_query(referral)

        # Step 3: Apply hybrid retrieval or fallback to basic matching
        if use_hybrid and query.strip():
            matches = self.hybrid_retrieval.search(query, feasible_psychologists, limit)
        else:
            matches = self._basic_matching(referral, feasible_psychologists, limit)

        # Step 4: Apply additional structured filters
        matches = self._apply_structured_filters(matches, referral)

        # Step 5: Apply probability calibration if enabled
        if self.calibration_service and self.calibration_service.is_fitted:
            matches = self._apply_calibration(matches)

        # Step 6: Add feasibility explanation to each match
        for match in matches:
            match["explanation"].update(
                {
                    "feasibility_passed": True,
                    "service_type_match": True,
                    "modality_match": True,
                    "radius_match": True,
                    "capacity_available": True,
                    "calibrated": self.calibration_service is not None
                    and self.calibration_service.is_fitted,
                }
            )

        # Step 7: Apply threshold routing
        routing_decision = self._apply_threshold_routing(matches, referral)

        # Step 8: Route the referral based on decision
        from matching.routing_service import ReferralRoutingService

        routing_service = ReferralRoutingService()
        routing_success = routing_service.route_referral(referral, routing_decision)

        if not routing_success:
            self.logger.warning(
                f"Failed to route referral {referral.id}, keeping in matching status"
            )

        self.logger.info(f"Found {len(matches)} matches for referral {referral.id}")
        return matches, routing_decision

    def _create_search_query(self, referral: Referral) -> str:
        """
        Create search query from referral information.

        Args:
            referral: The referral to create query for

        Returns:
            Search query string
        """
        query_parts = []

        # Add condition/issue description
        if referral.presenting_problem:
            query_parts.append(referral.presenting_problem)
        elif referral.condition_description:
            query_parts.append(referral.condition_description)

        # Add specialism requirements
        if referral.required_specialisms:
            query_parts.extend(referral.required_specialisms)

        # Add language requirements
        if referral.language_requirements:
            query_parts.extend(referral.language_requirements)

        # Add age group
        if referral.patient_age_group:
            query_parts.append(referral.patient_age_group)

        return " ".join(query_parts)

    def _basic_matching(
        self, referral: Referral, psychologists: QuerySet[Psychologist], limit: int
    ) -> list[dict[str, Any]]:
        """
        Basic matching without hybrid retrieval (fallback).

        Args:
            referral: The referral to match
            psychologists: QuerySet of feasible psychologists
            limit: Maximum number of matches to return

        Returns:
            List of match dictionaries
        """
        matches = []

        for psychologist in psychologists[:limit]:
            # Calculate basic structured score
            score = self._calculate_structured_score(psychologist, referral)

            match = {
                "psychologist": psychologist,
                "score": score,
                "vector_score": 0.0,
                "bm25_score": 0.0,
                "explanation": {
                    "hybrid_search": False,
                    "basic_matching": True,
                    "structured_score": score,
                },
            }
            matches.append(match)

        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    def _calculate_structured_score(
        self, psychologist: Psychologist, referral: Referral
    ) -> float:
        """
        Calculate structured feature matching score.

        Args:
            psychologist: Psychologist to score
            referral: Referral to match against

        Returns:
            Score between 0 and 1
        """
        score = 0.0
        total_weight = 0.0

        # Specialism matching (weight: 0.4)
        if referral.required_specialisms:
            specialism_score = self._calculate_specialism_score(psychologist, referral)
            score += specialism_score * 0.4
            total_weight += 0.4

        # Language matching (weight: 0.2)
        if referral.language_requirements:
            language_score = self._calculate_language_score(psychologist, referral)
            score += language_score * 0.2
            total_weight += 0.2

        # Age group matching (weight: 0.2)
        if referral.patient_age_group:
            age_score = self._calculate_age_score(psychologist, referral)
            score += age_score * 0.2
            total_weight += 0.2

        # Experience matching (weight: 0.2)
        experience_score = self._calculate_experience_score(psychologist, referral)
        score += experience_score * 0.2
        total_weight += 0.2

        # Normalize by total weight
        if total_weight > 0:
            score = score / total_weight

        return min(score, 1.0)

    def _calculate_specialism_score(
        self, psychologist: Psychologist, referral: Referral
    ) -> float:
        """Calculate specialism matching score."""
        if not psychologist.specialisms:
            return 0.0

        required_matches = 0
        preferred_matches = 0

        if referral.required_specialisms:
            for req_spec in referral.required_specialisms:
                if req_spec in psychologist.specialisms:
                    required_matches += 1

        if referral.required_specialisms:
            for pref_spec in referral.required_specialisms:
                if pref_spec in psychologist.specialisms:
                    preferred_matches += 1

        # Calculate score
        total_required = (
            len(referral.required_specialisms) if referral.required_specialisms else 0
        )
        total_preferred = (
            len(referral.required_specialisms) if referral.required_specialisms else 0
        )

        if total_required == 0 and total_preferred == 0:
            return 1.0  # No specialism requirements

        required_score = (
            required_matches / total_required if total_required > 0 else 1.0
        )
        preferred_score = (
            preferred_matches / total_preferred if total_preferred > 0 else 1.0
        )

        # Weight required more heavily
        return (required_score * 0.7) + (preferred_score * 0.3)

    def _calculate_language_score(
        self, psychologist: Psychologist, referral: Referral
    ) -> float:
        """Calculate language matching score."""
        if not referral.language_requirements or not psychologist.languages:
            return 1.0

        matches = 0
        for req_lang in referral.language_requirements:
            if req_lang in psychologist.languages:
                matches += 1

        return matches / len(referral.language_requirements)

    def _calculate_age_score(
        self, psychologist: Psychologist, referral: Referral
    ) -> float:
        """Calculate age group matching score."""
        if not referral.patient_age_group or not psychologist.preferred_age_groups:
            return 1.0

        if referral.patient_age_group in psychologist.preferred_age_groups:
            return 1.0

        return 0.0

    def _calculate_experience_score(
        self, psychologist: Psychologist, referral: Referral
    ) -> float:
        """Calculate experience matching score."""
        if not psychologist.years_experience:
            return 0.5  # Neutral score for unknown experience

        # Simple scoring based on experience level
        if psychologist.years_experience >= 10:
            return 1.0
        elif psychologist.years_experience >= 5:
            return 0.8
        elif psychologist.years_experience >= 2:
            return 0.6
        else:
            return 0.4

    def _apply_structured_filters(
        self, matches: list[dict[str, Any]], referral: Referral
    ) -> list[dict[str, Any]]:
        """
        Apply additional structured filters to matches.

        Args:
            matches: List of matches to filter
            referral: Referral to filter against

        Returns:
            Filtered list of matches
        """
        filtered_matches = []

        for match in matches:
            psychologist = match["psychologist"]

            # Apply specialism filter
            if referral.required_specialisms:
                if not any(
                    spec in psychologist.specialisms
                    for spec in referral.required_specialisms
                ):
                    continue

            # Apply language filter
            if referral.language_requirements:
                if not any(
                    lang in psychologist.languages
                    for lang in referral.language_requirements
                ):
                    continue

            # Apply age group filter
            if referral.patient_age_group and psychologist.preferred_age_groups:
                if referral.patient_age_group not in psychologist.preferred_age_groups:
                    continue

            filtered_matches.append(match)

        return filtered_matches

    def _apply_calibration(self, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Apply probability calibration to matches.

        Args:
            matches: List of matches to calibrate

        Returns:
            List of matches with calibrated scores
        """
        if not self.calibration_service or not self.calibration_service.is_fitted:
            return matches

        try:
            # Extract raw scores
            raw_scores = np.array([match["score"] for match in matches])

            # Calibrate scores
            calibrated_scores = self.calibration_service.calibrate_scores(raw_scores)

            # Update matches with calibrated scores
            for i, match in enumerate(matches):
                match["raw_score"] = match["score"]
                match["score"] = float(calibrated_scores[i])
                match["explanation"]["calibrated_score"] = float(calibrated_scores[i])
                match["explanation"]["raw_score"] = float(raw_scores[i])

            # Re-sort by calibrated scores
            matches.sort(key=lambda x: x["score"], reverse=True)

            self.logger.info(f"Applied calibration to {len(matches)} matches")
            return matches

        except Exception as e:
            self.logger.error(f"Failed to apply calibration: {e}")
            return matches

    def train_calibration_model(
        self, training_data: list[dict[str, Any]], calibration_type: str = "isotonic"
    ) -> bool:
        """
        Train a calibration model on historical data.

        Args:
            training_data: List of training examples with 'score' and 'outcome' keys
            calibration_type: Type of calibration ('isotonic' or 'platt')

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract scores and labels
            scores = np.array([item["score"] for item in training_data])
            labels = np.array([item["outcome"] for item in training_data])

            # Create new calibration service
            self.calibration_service = ProbabilityCalibrationService(calibration_type)

            # Fit the model
            success = self.calibration_service.fit(scores, labels)

            if success:
                self.logger.info(
                    f"Trained {calibration_type} calibration model on {len(training_data)} samples"
                )

                # Calculate and log metrics
                metrics = self.calibration_service.get_calibration_metrics(
                    scores, labels
                )
                self.logger.info(f"Calibration metrics: {metrics}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to train calibration model: {e}")
            return False

    def get_calibration_metrics(
        self, test_data: list[dict[str, Any]]
    ) -> dict[str, float]:
        """
        Get calibration metrics on test data.

        Args:
            test_data: List of test examples with 'score' and 'outcome' keys

        Returns:
            Dictionary of calibration metrics
        """
        if not self.calibration_service or not self.calibration_service.is_fitted:
            return {}

        try:
            scores = np.array([item["score"] for item in test_data])
            labels = np.array([item["outcome"] for item in test_data])

            return self.calibration_service.get_calibration_metrics(scores, labels)

        except Exception as e:
            self.logger.error(f"Failed to calculate calibration metrics: {e}")
            return {}

    def _apply_threshold_routing(
        self, matches: list[dict[str, Any]], referral: Referral
    ) -> dict[str, Any]:
        """
        Apply threshold routing to determine if referral should go to High-Touch queue.

        Args:
            matches: List of matches with scores
            referral: The referral being processed

        Returns:
            Dictionary with routing decision and details
        """
        try:
            # Get thresholds for the referrer's user type
            from matching.models import MatchingThreshold

            # Determine user type based on referrer role
            user_type = self._get_user_type_for_referrer(referral.referrer)

            # Get active thresholds for this user type (with caching)
            cache_key = f"threshold_config_{user_type}"
            threshold_config = cache.get(cache_key)

            if threshold_config is None:
                threshold_config = MatchingThreshold.objects.filter(
                    user_type=user_type, is_active=True
                ).first()
                if threshold_config:
                    cache.set(cache_key, threshold_config, 3600)  # Cache for 1 hour

            if not threshold_config:
                # Use default thresholds if none configured
                auto_threshold = 0.7
                high_touch_threshold = 0.5
                self.logger.warning(
                    f"No threshold config found for user type {user_type}, using defaults"
                )
            else:
                auto_threshold = threshold_config.auto_threshold
                high_touch_threshold = threshold_config.high_touch_threshold

            # Get the highest confidence score
            if not matches:
                highest_score = 0.0
            else:
                highest_score = max(match["score"] for match in matches)

            # Determine routing decision
            if highest_score >= auto_threshold:
                routing_decision = "auto"
                reason = f"Highest score {highest_score:.3f} >= auto threshold {auto_threshold:.3f}"
            elif highest_score >= high_touch_threshold:
                routing_decision = "high_touch"
                reason = f"Highest score {highest_score:.3f} >= high-touch threshold {high_touch_threshold:.3f}"
            else:
                routing_decision = "manual_review"
                reason = f"Highest score {highest_score:.3f} < high-touch threshold {high_touch_threshold:.3f}"

            routing_info = {
                "decision": routing_decision,
                "reason": reason,
                "highest_score": highest_score,
                "auto_threshold": auto_threshold,
                "high_touch_threshold": high_touch_threshold,
                "user_type": user_type,
                "match_count": len(matches),
            }

            self.logger.info(
                f"Threshold routing for referral {referral.id}: {routing_decision} - {reason}"
            )
            return routing_info

        except Exception as e:
            self.logger.error(f"Failed to apply threshold routing: {e}")
            return {
                "decision": "manual_review",
                "reason": f"Error in threshold routing: {str(e)}",
                "highest_score": 0.0,
                "auto_threshold": 0.7,
                "high_touch_threshold": 0.5,
                "user_type": "unknown",
                "match_count": len(matches),
            }

    def _get_user_type_for_referrer(self, referrer) -> str:
        """
        Determine user type for threshold routing based on referrer.

        Args:
            referrer: The user making the referral

        Returns:
            User type string for threshold lookup
        """
        # This is a simplified mapping - in a real system you'd check user roles/groups
        if hasattr(referrer, "role"):
            role = referrer.role
            if role in ["gp", "doctor", "referrer"]:
                return "gp"
            elif role in ["patient"]:
                return "patient"
            elif role in ["psychologist"]:
                return "psychologist"
            elif role in ["admin", "administrator"]:
                return "admin"

        # Default to GP for now
        return "gp"
