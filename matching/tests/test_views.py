"""
Tests for matching views.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from referrals.models import Referral
from catalogue.models import Psychologist
from matching.models import MatchingThreshold
import json

User = get_user_model()


class TestMatchingViews(TestCase):
    """Test matching views."""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
        
        # Create test users
        self.gp_user = User.objects.create_user(
            username='gp_user',
            email='gp@example.com',
            user_type='gp',
            password='testpass123'
        )
        self.patient_user = User.objects.create_user(
            username='patient_user',
            email='patient@example.com',
            user_type='patient',
            password='testpass123'
        )
        self.psychologist_user = User.objects.create_user(
            username='psych_user',
            email='psych@example.com',
            user_type='psychologist',
            password='testpass123'
        )
        
        # Create test referral
        self.referral = Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Anxiety and depression",
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.REMOTE,
            required_specialisms=['anxiety', 'depression']
        )
        
        # Create test psychologist
        self.psychologist = Psychologist.objects.create(
            user=self.psychologist_user,
            specialisms=['anxiety', 'depression'],
            service_type='nhs',
            modality='remote',
            is_active=True,
            is_accepting_referrals=True
        )
        
        # Create default thresholds
        MatchingThreshold.objects.create(
            user_type='gp',
            auto_threshold=0.7,
            high_touch_threshold=0.5
        )
    
    def tearDown(self):
        cache.clear()
    
    def test_matching_dashboard_requires_login(self):
        """Test that matching dashboard requires login."""
        response = self.client.get(reverse('matching:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_matching_dashboard_authenticated(self):
        """Test matching dashboard for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        response = self.client.get(reverse('matching:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matching Dashboard')
    
    def test_find_matches_api_requires_login(self):
        """Test that find matches API requires login."""
        response = self.client.post(
            reverse('matching:find_matches'),
            {'referral_id': str(self.referral.id)},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_find_matches_api_authenticated(self):
        """Test find matches API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.post(
            reverse('matching:find_matches'),
            {'referral_id': str(self.referral.id)},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('matches', data)
        self.assertIn('routing_decision', data)
    
    def test_find_matches_api_invalid_referral(self):
        """Test find matches API with invalid referral ID."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.post(
            reverse('matching:find_matches'),
            {'referral_id': 'invalid-id'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_find_matches_api_missing_referral_id(self):
        """Test find matches API with missing referral ID."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.post(
            reverse('matching:find_matches'),
            {},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_routing_statistics_api_requires_login(self):
        """Test that routing statistics API requires login."""
        response = self.client.get(reverse('matching:routing_statistics'))
        self.assertEqual(response.status_code, 401)
    
    def test_routing_statistics_api_authenticated(self):
        """Test routing statistics API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.get(reverse('matching:routing_statistics'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('total_referrals', data)
        self.assertIn('auto_routed', data)
        self.assertIn('high_touch_routed', data)
        self.assertIn('manual_review', data)
    
    def test_high_touch_queue_api_requires_login(self):
        """Test that high-touch queue API requires login."""
        response = self.client.get(reverse('matching:high_touch_queue'))
        self.assertEqual(response.status_code, 401)
    
    def test_high_touch_queue_api_authenticated(self):
        """Test high-touch queue API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        # Create a referral in high-touch queue
        high_touch_referral = Referral.objects.create(
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="High-touch case",
            status=Referral.Status.HIGH_TOUCH_QUEUE
        )
        
        response = self.client.get(reverse('matching:high_touch_queue'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('referrals', data)
        self.assertEqual(len(data['referrals']), 1)
        self.assertEqual(data['referrals'][0]['id'], str(high_touch_referral.id))
    
    def test_clear_cache_api_requires_login(self):
        """Test that clear cache API requires login."""
        response = self.client.post(reverse('matching:clear_cache'))
        self.assertEqual(response.status_code, 401)
    
    def test_clear_cache_api_authenticated(self):
        """Test clear cache API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        # Set some cache values
        cache.set('test_key', 'test_value', 3600)
        self.assertIsNotNone(cache.get('test_key'))
        
        response = self.client.post(reverse('matching:clear_cache'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
    
    def test_threshold_config_api_requires_login(self):
        """Test that threshold config API requires login."""
        response = self.client.get(reverse('matching:threshold_config'))
        self.assertEqual(response.status_code, 401)
    
    def test_threshold_config_api_authenticated(self):
        """Test threshold config API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.get(reverse('matching:threshold_config'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('thresholds', data)
        self.assertEqual(len(data['thresholds']), 1)
        self.assertEqual(data['thresholds'][0]['user_type'], 'gp')
    
    def test_update_threshold_api_requires_login(self):
        """Test that update threshold API requires login."""
        response = self.client.post(
            reverse('matching:update_threshold'),
            {'user_type': 'gp', 'auto_threshold': 0.8, 'high_touch_threshold': 0.6},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
    
    def test_update_threshold_api_authenticated(self):
        """Test update threshold API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.post(
            reverse('matching:update_threshold'),
            {'user_type': 'gp', 'auto_threshold': 0.8, 'high_touch_threshold': 0.6},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Verify threshold was updated
        threshold = MatchingThreshold.objects.get(user_type='gp')
        self.assertEqual(threshold.auto_threshold, 0.8)
        self.assertEqual(threshold.high_touch_threshold, 0.6)
    
    def test_update_threshold_api_invalid_data(self):
        """Test update threshold API with invalid data."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.post(
            reverse('matching:update_threshold'),
            {'user_type': 'invalid', 'auto_threshold': 0.8, 'high_touch_threshold': 0.6},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_performance_metrics_api_requires_login(self):
        """Test that performance metrics API requires login."""
        response = self.client.get(reverse('matching:performance_metrics'))
        self.assertEqual(response.status_code, 401)
    
    def test_performance_metrics_api_authenticated(self):
        """Test performance metrics API for authenticated user."""
        self.client.login(username='gp_user', password='testpass123')
        
        response = self.client.get(reverse('matching:performance_metrics'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('cache_stats', data)
        self.assertIn('matching_stats', data)
    
    def test_user_permissions(self):
        """Test that only authorized users can access matching features."""
        # Test with patient user (should have limited access)
        self.client.login(username='patient_user', password='testpass123')
        
        response = self.client.get(reverse('matching:dashboard'))
        self.assertEqual(response.status_code, 200)  # Should be able to view
        
        response = self.client.post(reverse('matching:clear_cache'))
        self.assertEqual(response.status_code, 403)  # Should not be able to clear cache
        
        # Test with psychologist user
        self.client.login(username='psych_user', password='testpass123')
        
        response = self.client.get(reverse('matching:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('matching:clear_cache'))
        self.assertEqual(response.status_code, 200)  # Should be able to clear cache
