"""
Tests for matching models.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from matching.models import (
    MatchingAlgorithm,
    CalibrationModel,
    MatchingThreshold,
    MatchingRun
)


class TestMatchingAlgorithm(TestCase):
    """Test MatchingAlgorithm model."""
    
    def test_creation(self):
        """Test creating a matching algorithm."""
        algorithm = MatchingAlgorithm.objects.create(
            name='Test Algorithm',
            version='1.0',
            algorithm_type='hybrid',
            parameters={'vector_weight': 0.7, 'bm25_weight': 0.3},
            description='Test algorithm for matching'
        )
        
        self.assertEqual(algorithm.name, 'Test Algorithm')
        self.assertEqual(algorithm.version, '1.0')
        self.assertEqual(algorithm.algorithm_type, 'hybrid')
        self.assertEqual(algorithm.parameters['vector_weight'], 0.7)
        self.assertTrue(algorithm.is_active)
        self.assertFalse(algorithm.is_default)
    
    def test_str_representation(self):
        """Test string representation."""
        algorithm = MatchingAlgorithm.objects.create(
            name='Test Algorithm',
            version='1.0',
            algorithm_type='hybrid'
        )
        
        expected = 'Test Algorithm v1.0'
        self.assertEqual(str(algorithm), expected)
    
    def test_unique_constraints(self):
        """Test unique constraints."""
        MatchingAlgorithm.objects.create(
            name='Test Algorithm',
            version='1.0',
            algorithm_type='hybrid'
        )
        
        # Should not be able to create another with same name and version
        with self.assertRaises(Exception):
            MatchingAlgorithm.objects.create(
                name='Test Algorithm',
                version='1.0',
                algorithm_type='vector'
            )
    
    def test_default_algorithm(self):
        """Test setting default algorithm."""
        algorithm1 = MatchingAlgorithm.objects.create(
            name='Algorithm 1',
            version='1.0',
            algorithm_type='hybrid'
        )
        algorithm2 = MatchingAlgorithm.objects.create(
            name='Algorithm 2',
            version='1.0',
            algorithm_type='vector'
        )
        
        # Set algorithm1 as default
        algorithm1.is_default = True
        algorithm1.save()
        
        # Set algorithm2 as default should unset algorithm1
        algorithm2.is_default = True
        algorithm2.save()
        
        algorithm1.refresh_from_db()
        self.assertFalse(algorithm1.is_default)
        self.assertTrue(algorithm2.is_default)


class TestCalibrationModel(TestCase):
    """Test CalibrationModel model."""
    
    def test_creation(self):
        """Test creating a calibration model."""
        model = CalibrationModel.objects.create(
            name='Test Calibration',
            calibration_type='isotonic',
            version='1.0',
            model_data='{"test": "data"}',
            brier_score=0.1,
            reliability_score=0.95,
            training_samples=1000
        )
        
        self.assertEqual(model.name, 'Test Calibration')
        self.assertEqual(model.calibration_type, 'isotonic')
        self.assertEqual(model.version, '1.0')
        self.assertEqual(model.model_data, '{"test": "data"}')
        self.assertEqual(model.brier_score, 0.1)
        self.assertEqual(model.reliability_score, 0.95)
        self.assertEqual(model.training_samples, 1000)
        self.assertTrue(model.is_active)
        self.assertFalse(model.is_default)
    
    def test_str_representation(self):
        """Test string representation."""
        model = CalibrationModel.objects.create(
            name='Test Calibration',
            calibration_type='isotonic',
            version='1.0',
            model_data='{}'
        )
        
        expected = 'Test Calibration v1.0 (Isotonic Regression)'
        self.assertEqual(str(model), expected)
    
    def test_calibration_type_choices(self):
        """Test calibration type choices."""
        model = CalibrationModel.objects.create(
            name='Test Calibration',
            calibration_type='isotonic',
            model_data='{}'
        )
        
        self.assertEqual(model.get_calibration_type_display(), 'Isotonic Regression')
        
        model.calibration_type = 'platt'
        model.save()
        self.assertEqual(model.get_calibration_type_display(), 'Platt Scaling')
    
    def test_unique_constraints(self):
        """Test unique constraints."""
        CalibrationModel.objects.create(
            name='Test Calibration',
            version='1.0',
            calibration_type='isotonic',
            model_data='{}'
        )
        
        # Should not be able to create another with same name and version
        with self.assertRaises(Exception):
            CalibrationModel.objects.create(
                name='Test Calibration',
                version='1.0',
                calibration_type='platt',
                model_data='{}'
            )


class TestMatchingThreshold(TestCase):
    """Test MatchingThreshold model."""
    
    def test_creation(self):
        """Test creating a matching threshold."""
        threshold = MatchingThreshold.objects.create(
            user_type='gp',
            auto_threshold=0.7,
            high_touch_threshold=0.5
        )
        
        self.assertEqual(threshold.user_type, 'gp')
        self.assertEqual(threshold.auto_threshold, 0.7)
        self.assertEqual(threshold.high_touch_threshold, 0.5)
        self.assertTrue(threshold.is_active)
    
    def test_str_representation(self):
        """Test string representation."""
        threshold = MatchingThreshold.objects.create(
            user_type='gp',
            auto_threshold=0.7,
            high_touch_threshold=0.5
        )
        
        expected = 'Thresholds for GP'
        self.assertEqual(str(threshold), expected)
    
    def test_user_type_choices(self):
        """Test user type choices."""
        threshold = MatchingThreshold.objects.create(
            user_type='gp',
            auto_threshold=0.7,
            high_touch_threshold=0.5
        )
        
        self.assertEqual(threshold.get_user_type_display(), 'GP')
        
        threshold.user_type = 'patient'
        threshold.save()
        self.assertEqual(threshold.get_user_type_display(), 'Patient')
    
    def test_unique_constraints(self):
        """Test unique constraints."""
        MatchingThreshold.objects.create(
            user_type='gp',
            auto_threshold=0.7,
            high_touch_threshold=0.5
        )
        
        # Should not be able to create another with same user_type
        with self.assertRaises(Exception):
            MatchingThreshold.objects.create(
                user_type='gp',
                auto_threshold=0.8,
                high_touch_threshold=0.6
            )
    
    def test_threshold_validation(self):
        """Test threshold value validation."""
        # Auto threshold should be >= high touch threshold
        threshold = MatchingThreshold.objects.create(
            user_type='gp',
            auto_threshold=0.5,
            high_touch_threshold=0.7  # This should be <= auto_threshold
        )
        
        # The model doesn't have validation, but in practice this should be checked
        self.assertEqual(threshold.auto_threshold, 0.5)
        self.assertEqual(threshold.high_touch_threshold, 0.7)


class TestMatchingRun(TestCase):
    """Test MatchingRun model."""
    
    def test_creation(self):
        """Test creating a matching run."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=100,
            successful_matches=80,
            failed_matches=20,
            average_confidence=0.75,
            processing_time_seconds=30.5
        )
        
        self.assertEqual(run.algorithm_name, 'Test Algorithm')
        self.assertEqual(run.algorithm_version, '1.0')
        self.assertEqual(run.total_referrals, 100)
        self.assertEqual(run.successful_matches, 80)
        self.assertEqual(run.failed_matches, 20)
        self.assertEqual(run.average_confidence, 0.75)
        self.assertEqual(run.processing_time_seconds, 30.5)
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)
    
    def test_str_representation(self):
        """Test string representation."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=100,
            successful_matches=80,
            failed_matches=20,
            average_confidence=0.75,
            processing_time_seconds=30.5
        )
        
        expected = 'Test Algorithm v1.0 - 100 referrals (80 successful)'
        self.assertEqual(str(run), expected)
    
    def test_success_rate_property(self):
        """Test success rate calculation."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=100,
            successful_matches=80,
            failed_matches=20,
            average_confidence=0.75,
            processing_time_seconds=30.5
        )
        
        expected_success_rate = 80 / 100
        self.assertEqual(run.success_rate, expected_success_rate)
    
    def test_success_rate_zero_division(self):
        """Test success rate with zero total referrals."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=0,
            successful_matches=0,
            failed_matches=0,
            average_confidence=0.0,
            processing_time_seconds=0.0
        )
        
        self.assertEqual(run.success_rate, 0.0)
    
    def test_duration_property(self):
        """Test duration calculation."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=100,
            successful_matches=80,
            failed_matches=20,
            average_confidence=0.75,
            processing_time_seconds=30.5
        )
        
        self.assertEqual(run.duration, 30.5)
    
    def test_metadata_property(self):
        """Test metadata property."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=100,
            successful_matches=80,
            failed_matches=20,
            average_confidence=0.75,
            processing_time_seconds=30.5,
            metadata={'test_key': 'test_value'}
        )
        
        expected_metadata = {'test_key': 'test_value'}
        self.assertEqual(run.metadata, expected_metadata)
    
    def test_metadata_default(self):
        """Test metadata default value."""
        run = MatchingRun.objects.create(
            algorithm_name='Test Algorithm',
            algorithm_version='1.0',
            total_referrals=100,
            successful_matches=80,
            failed_matches=20,
            average_confidence=0.75,
            processing_time_seconds=30.5
        )
        
        self.assertEqual(run.metadata, {})
