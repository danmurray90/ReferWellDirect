"""
Tests for matching services.
"""
from unittest.mock import Mock, patch

import numpy as np

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from catalogue.models import Psychologist
from matching.routing_service import ReferralRoutingService
from matching.services import (
    BM25Service,
    FeasibilityFilter,
    HybridRetrievalService,
    MatchingService,
    ProbabilityCalibrationService,
    VectorEmbeddingService,
)
from referrals.models import Referral

User = get_user_model()


class TestVectorEmbeddingService(TestCase):
    """Test VectorEmbeddingService."""

    def setUp(self):
        self.service = VectorEmbeddingService()
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch("sentence_transformers.SentenceTransformer")
    def test_initialization(self, mock_transformer):
        """Test service initialization."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        service = VectorEmbeddingService(model_name="test-model")

        self.assertEqual(service.model_name, "test-model")
        self.assertEqual(service.cache_timeout, 3600)
        mock_transformer.assert_called_once_with("test-model")

    @patch("sentence_transformers.SentenceTransformer")
    def test_generate_embedding_caching(self, mock_transformer):
        """Test embedding generation with caching."""
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model

        service = VectorEmbeddingService()
        service.model = mock_model

        text = "test text"

        # First call - should not be cached
        result1 = service.generate_embedding(text)

        # Second call - should be cached
        result2 = service.generate_embedding(text)

        # Model should only be called once due to caching
        mock_model.encode.assert_called()

        # Results should be the same
        np.testing.assert_array_equal(result1, result2)
        np.testing.assert_array_equal(result1, mock_embedding)

    @patch("sentence_transformers.SentenceTransformer")
    def test_generate_embeddings_batch_caching(self, mock_transformer):
        """Test batch embedding generation with caching."""
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        service = VectorEmbeddingService()
        service.model = mock_model

        texts = ["text1", "text2"]

        # First call
        result1 = service.generate_embeddings_batch(texts)

        # Second call - should use cache
        result2 = service.generate_embeddings_batch(texts)

        # Model should only be called once
        mock_model.encode.assert_called()

        # Results should be the same
        np.testing.assert_array_equal(result1, result2)

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        embedding1 = np.array([1, 0, 0])
        embedding2 = np.array([0, 1, 0])
        embedding3 = np.array([1, 0, 0])

        # Orthogonal vectors should have similarity 0
        similarity = self.service.calculate_similarity(embedding1, embedding2)
        self.assertAlmostEqual(similarity, 0.0, places=5)

        # Identical vectors should have similarity 1
        similarity = self.service.calculate_similarity(embedding1, embedding3)
        self.assertAlmostEqual(similarity, 1.0, places=5)


class TestBM25Service(TestCase):
    """Test BM25Service."""

    def setUp(self):
        self.service = BM25Service()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.cache_timeout, 1800)
        self.assertIsNone(self.service.vectorizer)
        self.assertIsNone(self.service.document_vectors)
        self.assertEqual(self.service.document_ids, [])

    def test_build_index_empty(self):
        """Test building index with empty queryset."""
        from django.db.models import QuerySet

        empty_qs = QuerySet(Psychologist)

        result = self.service.build_index(empty_qs)

        self.assertFalse(result)
        self.assertIsNone(self.service.vectorizer)

    @patch("matching.services.TfidfVectorizer")
    def test_build_index_success(self, mock_vectorizer):
        """Test successful index building."""
        # Create mock psychologist
        user = User.objects.create_user(
            username="test_psych",
            email="test@example.com",
            first_name="Test",
            last_name="Psychologist",
        )
        psychologist = Psychologist.objects.create(
            user=user,
            specialisms=["anxiety", "depression"],
            qualifications=["PhD"],
            preferred_conditions=["anxiety"],
        )

        mock_vectorizer_instance = Mock()
        mock_vectorizer.return_value = mock_vectorizer_instance
        mock_vectorizer_instance.fit_transform.return_value = np.array([[1, 2], [3, 4]])

        result = self.service.build_index(
            Psychologist.objects.filter(id=psychologist.id)
        )

        self.assertTrue(result)
        self.assertEqual(len(self.service.document_ids), 1)
        self.assertEqual(self.service.document_ids[0], psychologist.id)

    def test_search_no_index(self):
        """Test search without built index."""
        result = self.service.search("test query")
        self.assertEqual(result, [])

    @patch("matching.services.TfidfVectorizer")
    def test_search_caching(self, mock_vectorizer):
        """Test search with caching."""
        # Build index
        user = User.objects.create_user(
            username="test_psych",
            email="test@example.com",
            first_name="Test",
            last_name="Psychologist",
        )
        psychologist = Psychologist.objects.create(
            user=user, specialisms=["anxiety", "depression"]
        )

        mock_vectorizer_instance = Mock()
        mock_vectorizer.return_value = mock_vectorizer_instance
        mock_vectorizer_instance.fit_transform.return_value = np.array([[1, 2]])
        mock_vectorizer_instance.transform.return_value = np.array([[0.5, 1.0]])

        self.service.build_index(Psychologist.objects.filter(id=psychologist.id))

        query = "anxiety therapy"

        # First search
        result1 = self.service.search(query, top_k=1)

        # Second search - should use cache
        result2 = self.service.search(query, top_k=1)

        # Vectorizer should only be called once for transform
        self.assertGreaterEqual(mock_vectorizer_instance.transform.call_count, 1)

        # Results should be the same
        self.assertEqual(result1, result2)


class TestHybridRetrievalService(TestCase):
    """Test HybridRetrievalService."""

    def setUp(self):
        self.service = HybridRetrievalService(vector_weight=0.7, bm25_weight=0.3)
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.vector_weight, 0.7)
        self.assertEqual(self.service.bm25_weight, 0.3)

    @patch("matching.services.VectorEmbeddingService")
    @patch("matching.services.BM25Service")
    def test_search_hybrid(self, mock_bm25, mock_vector):
        """Test hybrid search."""
        # Create mock psychologist
        user = User.objects.create_user(
            username="test_psych",
            email="test@example.com",
            first_name="Test",
            last_name="Psychologist",
        )
        psychologist = Psychologist.objects.create(user=user, specialisms=["anxiety"])

        # Mock services
        mock_vector_instance = Mock()
        mock_vector.return_value = mock_vector_instance
        mock_vector_instance.generate_embedding.return_value = np.array([0.1, 0.2])

        mock_bm25_instance = Mock()
        mock_bm25.return_value = mock_bm25_instance
        mock_bm25_instance.search.return_value = [(str(psychologist.id), 0.8)]

        # Mock psychologist methods
        psychologist.get_embedding = Mock(return_value=np.array([0.1, 0.2]))

        result = self.service.search(
            "anxiety therapy", Psychologist.objects.filter(id=psychologist.id), top_k=1
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["psychologist"], psychologist)
        self.assertIn("score", result[0])
        self.assertIn("vector_score", result[0])
        self.assertIn("bm25_score", result[0])


class TestFeasibilityFilter(TestCase):
    """Test FeasibilityFilter."""

    def setUp(self):
        self.filter = FeasibilityFilter()

        # Create test users
        self.gp_user = User.objects.create_user(
            username="gp_user", email="gp@example.com", user_type="gp"
        )
        self.patient_user = User.objects.create_user(
            username="patient_user", email="patient@example.com", user_type="patient"
        )

        # Create test referral
        self.referral = Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Anxiety and depression",
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.REMOTE,
            preferred_latitude=51.5074,
            preferred_longitude=-0.1278,
            max_distance_km=50,
            required_specialisms=["anxiety", "depression"],
        )

    def test_filter_psychologists_basic(self):
        """Test basic filtering."""
        # Create test psychologist
        psych_user = User.objects.create_user(
            username="psych_user", email="psych@example.com", user_type="psychologist"
        )
        psychologist = Psychologist.objects.create(
            user=psych_user,
            specialisms=["anxiety", "depression"],
            service_type="nhs",
            modality="remote",
            is_active=True,
            is_accepting_referrals=True,
        )

        result = self.filter.filter_psychologists(self.referral)

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), psychologist)

    def test_filter_by_service_type(self):
        """Test filtering by service type."""
        # Create NHS psychologist
        nhs_user = User.objects.create_user(
            username="nhs_psych", email="nhs@example.com", user_type="psychologist"
        )
        nhs_psych = Psychologist.objects.create(
            user=nhs_user,
            service_type="nhs",
            is_active=True,
            is_accepting_referrals=True,
        )

        # Create private psychologist
        private_user = User.objects.create_user(
            username="private_psych",
            email="private@example.com",
            user_type="psychologist",
        )
        private_psych = Psychologist.objects.create(
            user=private_user,
            service_type="private",
            is_active=True,
            is_accepting_referrals=True,
        )

        # Test NHS referral
        result = self.filter.filter_psychologists(self.referral)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), nhs_psych)

        # Test private referral
        self.referral.service_type = Referral.ServiceType.PRIVATE
        self.referral.save()

        result = self.filter.filter_psychologists(self.referral)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), private_psych)


class TestProbabilityCalibrationService(TestCase):
    """Test ProbabilityCalibrationService."""

    def setUp(self):
        self.service = ProbabilityCalibrationService()

    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.calibration_type, "isotonic")
        self.assertIsNone(self.service.calibrator)
        self.assertFalse(self.service.is_fitted)

    def test_fit_isotonic(self):
        """Test fitting isotonic calibration."""
        scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        labels = np.array([0, 0, 1, 1, 1])

        result = self.service.fit(scores, labels)

        self.assertTrue(result)
        self.assertTrue(self.service.is_fitted)
        self.assertIsNotNone(self.service.calibrator)

    def test_fit_platt(self):
        """Test fitting Platt scaling."""
        service = ProbabilityCalibrationService(calibration_type="platt")
        scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        labels = np.array([0, 0, 1, 1, 1])

        result = service.fit(scores, labels)

        self.assertTrue(result)
        self.assertTrue(service.is_fitted)

    def test_calibrate_scores_not_fitted(self):
        """Test calibration without fitted model."""
        scores = np.array([0.5, 0.7, 0.9])
        result = self.service.calibrate_scores(scores)

        np.testing.assert_array_equal(result, scores)

    def test_calibrate_scores_fitted(self):
        """Test calibration with fitted model."""
        scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        labels = np.array([0, 0, 1, 1, 1])

        self.service.fit(scores, labels)
        result = self.service.calibrate_scores(scores)

        self.assertEqual(len(result), len(scores))
        # Calibrated scores should be in [0, 1] range
        self.assertTrue(np.all(result >= 0))
        self.assertTrue(np.all(result <= 1))


class TestMatchingService(TestCase):
    """Test MatchingService."""

    def setUp(self):
        self.service = MatchingService()
        cache.clear()

        # Create test users
        self.gp_user = User.objects.create_user(
            username="gp_user", email="gp@example.com", user_type="gp"
        )
        self.patient_user = User.objects.create_user(
            username="patient_user", email="patient@example.com", user_type="patient"
        )

        # Create test referral
        self.referral = Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Anxiety and depression",
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.REMOTE,
            required_specialisms=["anxiety", "depression"],
        )

    def tearDown(self):
        cache.clear()

    def test_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service.feasibility_filter)
        self.assertIsNotNone(self.service.hybrid_retrieval)
        self.assertIsNotNone(self.service.vector_service)
        self.assertIsNotNone(self.service.calibration_service)

    def test_create_search_query(self):
        """Test search query creation."""
        query = self.service._create_search_query(self.referral)

        self.assertIn("Anxiety and depression", query)
        self.assertIn("anxiety", query)
        self.assertIn("depression", query)

    def test_get_user_type_for_referrer(self):
        """Test user type determination."""
        # Test with role attribute
        self.gp_user.role = "gp"
        user_type = self.service._get_user_type_for_referrer(self.gp_user)
        self.assertEqual(user_type, "gp")

        # Test with different role
        self.gp_user.role = "doctor"
        user_type = self.service._get_user_type_for_referrer(self.gp_user)
        self.assertEqual(user_type, "gp")

        # Test without role attribute
        delattr(self.gp_user, "role")
        user_type = self.service._get_user_type_for_referrer(self.gp_user)
        self.assertEqual(user_type, "gp")  # Default


class TestReferralRoutingService(TestCase):
    """Test ReferralRoutingService."""

    def setUp(self):
        self.service = ReferralRoutingService()
        cache.clear()

        # Create test users
        self.gp_user = User.objects.create_user(
            username="gp_user", email="gp@example.com", user_type="gp"
        )
        self.patient_user = User.objects.create_user(
            username="patient_user", email="patient@example.com", user_type="patient"
        )

        # Create test referral
        self.referral = Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Test problem",
        )

    def tearDown(self):
        cache.clear()

    def test_route_referral_auto(self):
        """Test auto routing."""
        routing_decision = {"decision": "auto", "reason": "High confidence score"}

        result = self.service.route_referral(self.referral, routing_decision)

        self.assertTrue(result)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.SHORTLISTED)

    def test_route_referral_high_touch(self):
        """Test high-touch routing."""
        routing_decision = {
            "decision": "high_touch",
            "reason": "Medium confidence score",
        }

        result = self.service.route_referral(self.referral, routing_decision)

        self.assertTrue(result)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.HIGH_TOUCH_QUEUE)

    def test_route_referral_manual_review(self):
        """Test manual review routing."""
        routing_decision = {
            "decision": "manual_review",
            "reason": "Low confidence score",
        }

        result = self.service.route_referral(self.referral, routing_decision)

        self.assertTrue(result)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.MATCHING)

    def test_get_high_touch_queue(self):
        """Test getting high-touch queue."""
        # Create referrals in different statuses
        Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Problem 1",
            status=Referral.Status.HIGH_TOUCH_QUEUE,
        )
        Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Problem 2",
            status=Referral.Status.SUBMITTED,
        )

        queue = self.service.get_high_touch_queue()

        self.assertEqual(queue.count(), 1)
        self.assertEqual(queue.first().presenting_problem, "Problem 1")

    def test_create_default_thresholds(self):
        """Test creating default thresholds."""
        from matching.models import MatchingThreshold

        # Clear existing thresholds
        MatchingThreshold.objects.all().delete()

        result = self.service.create_default_thresholds()

        self.assertTrue(result)
        self.assertEqual(MatchingThreshold.objects.count(), 4)

        # Check specific thresholds
        gp_threshold = MatchingThreshold.objects.get(user_type="gp")
        self.assertEqual(gp_threshold.auto_threshold, 0.7)
        self.assertEqual(gp_threshold.high_touch_threshold, 0.5)

    def test_invalidate_threshold_cache(self):
        """Test cache invalidation."""
        # Set some cache values
        cache.set("threshold_config_gp", "test_value", 3600)
        cache.set("threshold_config_patient", "test_value", 3600)

        # Verify cache values are set
        self.assertIsNotNone(cache.get("threshold_config_gp"))
        self.assertIsNotNone(cache.get("threshold_config_patient"))

        # Invalidate specific user type
        self.service.invalidate_threshold_cache("gp")

        self.assertIsNone(cache.get("threshold_config_gp"))
        self.assertIsNotNone(cache.get("threshold_config_patient"))

        # Set patient cache again for the final test
        cache.set("threshold_config_patient", "test_value", 3600)

        # Invalidate all
        self.service.invalidate_threshold_cache()

        self.assertIsNone(cache.get("threshold_config_patient"))
