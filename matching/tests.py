"""
Tests for matching services.
"""
import pytest
from django.test import TestCase
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import numpy as np
from catalogue.models import Psychologist
from referrals.models import Referral
from matching.services import (
    FeasibilityFilter, 
    MatchingService, 
    VectorEmbeddingService, 
    BM25Service, 
    HybridRetrievalService
)

User = get_user_model()


class FeasibilityFilterTest(TestCase):
    """Test cases for the FeasibilityFilter class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.psychologist_user = User.objects.create_user(
            email='psychologist@example.com',
            password='testpass123',
            first_name='Dr. Test',
            last_name='Psychologist'
        )
        
        # Create a psychologist
        self.psychologist = Psychologist.objects.create(
            user=self.psychologist_user,
            service_type=Psychologist.ServiceType.MIXED,
            modality=Psychologist.Modality.MIXED,
            latitude=51.5074,  # London coordinates
            longitude=-0.1278,
            max_patients=50,
            current_patients=25,
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        
        # Update location for PostGIS
        self.psychologist.update_location()
        
        # Create a referral
        self.referral = Referral.objects.create(
            patient=self.user,
            preferred_service_type='nhs',
            preferred_modality='remote',
            patient_latitude=51.5074,  # Same as psychologist
            patient_longitude=-0.1278,
            max_distance_km=10
        )
        
        self.filter = FeasibilityFilter()
    
    def test_filter_by_service_type_nhs(self):
        """Test filtering by NHS service type."""
        # Test NHS preference
        referral = Referral.objects.create(
            patient=self.user,
            preferred_service_type='nhs',
            patient_latitude=51.5074,
            patient_longitude=-0.1278,
            max_distance_km=10
        )
        
        filtered = self.filter._filter_by_service_type(
            Psychologist.objects.all(), 
            referral
        )
        
        # Should include mixed and nhs psychologists
        assert filtered.count() == 1
        assert filtered.first().service_type in ['nhs', 'mixed']
    
    def test_filter_by_service_type_private(self):
        """Test filtering by private service type."""
        # Create a private-only psychologist
        private_psychologist = Psychologist.objects.create(
            user=User.objects.create_user(
                email='private@example.com',
                password='testpass123',
                first_name='Private',
                last_name='Psychologist'
            ),
            service_type=Psychologist.ServiceType.PRIVATE,
            modality=Psychologist.Modality.MIXED,
            latitude=51.5074,
            longitude=-0.1278,
            max_patients=50,
            current_patients=25,
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        private_psychologist.update_location()
        
        referral = Referral.objects.create(
            patient=self.user,
            preferred_service_type='private',
            patient_latitude=51.5074,
            patient_longitude=-0.1278,
            max_distance_km=10
        )
        
        filtered = self.filter._filter_by_service_type(
            Psychologist.objects.all(), 
            referral
        )
        
        # Should include mixed and private psychologists
        assert filtered.count() == 2
        for psych in filtered:
            assert psych.service_type in ['private', 'mixed']
    
    def test_filter_by_modality_remote(self):
        """Test filtering by remote modality."""
        referral = Referral.objects.create(
            patient=self.user,
            preferred_modality='remote',
            patient_latitude=51.5074,
            patient_longitude=-0.1278,
            max_distance_km=10
        )
        
        filtered = self.filter._filter_by_modality(
            Psychologist.objects.all(), 
            referral
        )
        
        # Should include mixed and remote psychologists
        assert filtered.count() == 1
        assert filtered.first().modality in ['remote', 'mixed']
    
    def test_filter_by_availability(self):
        """Test filtering by availability status."""
        # Create an unavailable psychologist
        unavailable_psychologist = Psychologist.objects.create(
            user=User.objects.create_user(
                email='unavailable@example.com',
                password='testpass123',
                first_name='Unavailable',
                last_name='Psychologist'
            ),
            service_type=Psychologist.ServiceType.MIXED,
            modality=Psychologist.Modality.MIXED,
            latitude=51.5074,
            longitude=-0.1278,
            max_patients=50,
            current_patients=25,
            availability_status=Psychologist.AvailabilityStatus.UNAVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        unavailable_psychologist.update_location()
        
        filtered = self.filter._filter_by_availability(
            Psychologist.objects.all(), 
            self.referral
        )
        
        # Should only include available psychologists
        assert filtered.count() == 1
        assert filtered.first().availability_status == Psychologist.AvailabilityStatus.AVAILABLE
    
    def test_filter_by_radius(self):
        """Test filtering by geographic radius."""
        # Create a psychologist far away
        far_psychologist = Psychologist.objects.create(
            user=User.objects.create_user(
                email='far@example.com',
                password='testpass123',
                first_name='Far',
                last_name='Psychologist'
            ),
            service_type=Psychologist.ServiceType.MIXED,
            modality=Psychologist.Modality.MIXED,
            latitude=52.0,  # Far from London
            longitude=0.0,
            max_patients=50,
            current_patients=25,
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        far_psychologist.update_location()
        
        referral = Referral.objects.create(
            patient=self.user,
            patient_latitude=51.5074,  # London
            patient_longitude=-0.1278,
            max_distance_km=5  # Small radius
        )
        
        filtered = self.filter._filter_by_radius(
            Psychologist.objects.all(), 
            referral
        )
        
        # Should only include nearby psychologists
        assert filtered.count() == 1
        assert filtered.first().id == self.psychologist.id
    
    def test_filter_by_capacity(self):
        """Test filtering by capacity."""
        # Create a full psychologist
        full_psychologist = Psychologist.objects.create(
            user=User.objects.create_user(
                email='full@example.com',
                password='testpass123',
                first_name='Full',
                last_name='Psychologist'
            ),
            service_type=Psychologist.ServiceType.MIXED,
            modality=Psychologist.Modality.MIXED,
            latitude=51.5074,
            longitude=-0.1278,
            max_patients=50,
            current_patients=50,  # At capacity
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        full_psychologist.update_location()
        
        filtered = self.filter._filter_by_capacity(
            Psychologist.objects.all(), 
            self.referral
        )
        
        # Should only include psychologists with capacity
        assert filtered.count() == 1
        assert filtered.first().id == self.psychologist.id
    
    def test_full_feasibility_filter(self):
        """Test the complete feasibility filter."""
        # Create a psychologist that should be filtered out
        unavailable_psychologist = Psychologist.objects.create(
            user=User.objects.create_user(
                email='unavailable@example.com',
                password='testpass123',
                first_name='Unavailable',
                last_name='Psychologist'
            ),
            service_type=Psychologist.ServiceType.PRIVATE,  # Wrong service type
            modality=Psychologist.Modality.IN_PERSON,  # Wrong modality
            latitude=52.0,  # Too far
            longitude=0.0,
            max_patients=50,
            current_patients=50,  # At capacity
            availability_status=Psychologist.AvailabilityStatus.UNAVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        unavailable_psychologist.update_location()
        
        filtered = self.filter.filter_psychologists(self.referral)
        
        # Should only include the original psychologist
        assert filtered.count() == 1
        assert filtered.first().id == self.psychologist.id


class MatchingServiceTest(TestCase):
    """Test cases for the MatchingService class."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.psychologist_user = User.objects.create_user(
            email='psychologist@example.com',
            password='testpass123',
            first_name='Dr. Test',
            last_name='Psychologist'
        )
        
        self.psychologist = Psychologist.objects.create(
            user=self.psychologist_user,
            service_type=Psychologist.ServiceType.MIXED,
            modality=Psychologist.Modality.MIXED,
            latitude=51.5074,
            longitude=-0.1278,
            max_patients=50,
            current_patients=25,
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
        self.psychologist.update_location()
        
        self.referral = Referral.objects.create(
            patient=self.user,
            preferred_service_type='nhs',
            preferred_modality='remote',
            patient_latitude=51.5074,
            patient_longitude=-0.1278,
            max_distance_km=10
        )
        
        self.matching_service = MatchingService()
    
    def test_find_matches(self):
        """Test finding matches for a referral."""
        matches = self.matching_service.find_matches(self.referral)
        
        assert len(matches) == 1
        assert matches[0]['psychologist'].id == self.psychologist.id
        assert matches[0]['score'] == 0.0  # Placeholder
        assert matches[0]['explanation']['feasibility_passed'] is True
    
    def test_find_matches_no_feasible_psychologists(self):
        """Test finding matches when no psychologists are feasible."""
        # Create a referral with impossible criteria
        impossible_referral = Referral.objects.create(
            patient=self.user,
            preferred_service_type='nhs',
            preferred_modality='remote',
            patient_latitude=60.0,  # Very far north
            patient_longitude=0.0,
            max_distance_km=1  # Very small radius
        )
        
        matches = self.matching_service.find_matches(impossible_referral)
        
        assert len(matches) == 0


class VectorEmbeddingServiceTest(TestCase):
    """Test cases for VectorEmbeddingService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='psychologist'
        )
        
        self.psychologist = Psychologist.objects.create(
            user=self.user,
            specialisms=['anxiety', 'depression'],
            qualifications=['PhD', 'Clinical Psychology'],
            preferred_conditions=['anxiety disorders']
        )
    
    @patch('matching.services.SentenceTransformer')
    def test_generate_embedding(self, mock_transformer):
        """Test embedding generation."""
        # Mock the transformer
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        service = VectorEmbeddingService()
        embedding = service.generate_embedding("test text")
        
        assert embedding.shape == (3,)
        mock_model.encode.assert_called_once_with("test text", convert_to_numpy=True)
    
    @patch('matching.services.SentenceTransformer')
    def test_update_psychologist_embedding(self, mock_transformer):
        """Test updating psychologist embedding."""
        # Mock the transformer
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        service = VectorEmbeddingService()
        success = service.update_psychologist_embedding(self.psychologist)
        
        assert success is True
        self.psychologist.refresh_from_db()
        assert self.psychologist.embedding is not None
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        service = VectorEmbeddingService()
        
        # Mock the model to avoid loading
        service.model = MagicMock()
        
        embedding1 = np.array([1, 0, 0])
        embedding2 = np.array([0, 1, 0])
        
        similarity = service.calculate_similarity(embedding1, embedding2)
        assert similarity == 0.0  # Orthogonal vectors


class BM25ServiceTest(TestCase):
    """Test cases for BM25Service."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='test1@example.com',
            password='testpass123',
            first_name='Test1',
            last_name='User1',
            role='psychologist'
        )
        
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
            first_name='Test2',
            last_name='User2',
            role='psychologist'
        )
        
        self.psychologist1 = Psychologist.objects.create(
            user=self.user1,
            specialisms=['anxiety', 'depression'],
            qualifications=['PhD']
        )
        
        self.psychologist2 = Psychologist.objects.create(
            user=self.user2,
            specialisms=['trauma', 'ptsd'],
            qualifications=['MSc']
        )
    
    def test_build_index(self):
        """Test building BM25 index."""
        service = BM25Service()
        psychologists = Psychologist.objects.all()
        
        success = service.build_index(psychologists)
        assert success is True
        assert service.vectorizer is not None
        assert service.document_vectors is not None
        assert len(service.document_ids) == 2
    
    def test_search(self):
        """Test BM25 search."""
        service = BM25Service()
        psychologists = Psychologist.objects.all()
        
        # Build index
        service.build_index(psychologists)
        
        # Search
        results = service.search("anxiety depression", top_k=2)
        
        assert isinstance(results, list)
        assert len(results) <= 2
        
        for psych_id, score in results:
            assert psych_id in [str(p.id) for p in psychologists]
            assert score >= 0.0


class HybridRetrievalServiceTest(TestCase):
    """Test cases for HybridRetrievalService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='psychologist'
        )
        
        self.psychologist = Psychologist.objects.create(
            user=self.user,
            specialisms=['anxiety', 'depression'],
            service_type='nhs',
            modality='mixed',
            location=Point(-0.1276, 51.5074, srid=4326),
            latitude=51.5074,
            longitude=-0.1276,
            max_patients=50,
            current_patients=25,
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True
        )
    
    @patch('matching.services.VectorEmbeddingService')
    @patch('matching.services.BM25Service')
    def test_search_hybrid(self, mock_bm25, mock_vector):
        """Test hybrid search."""
        # Mock services
        mock_vector_instance = MagicMock()
        mock_vector_instance.generate_embedding.return_value = np.array([0.1, 0.2, 0.3])
        mock_vector_instance.calculate_similarity.return_value = 0.8
        mock_vector.return_value = mock_vector_instance
        
        mock_bm25_instance = MagicMock()
        mock_bm25_instance.build_index.return_value = True
        mock_bm25_instance.search.return_value = [(str(self.psychologist.id), 0.6)]
        mock_bm25.return_value = mock_bm25_instance
        
        service = HybridRetrievalService()
        psychologists = Psychologist.objects.all()
        
        results = service.search("anxiety depression", psychologists, top_k=1)
        
        assert len(results) == 1
        assert results[0]['psychologist'] == self.psychologist
        assert results[0]['score'] > 0.0
        assert results[0]['explanation']['hybrid_search'] is True
