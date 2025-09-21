"""
Tests for referrals app.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Referral, Candidate, Appointment, Message, Task
import json

User = get_user_model()


class ReferralModelTest(TestCase):
    """
    Test cases for Referral model.
    """
    
    def setUp(self):
        self.referrer = User.objects.create_user(
            email='referrer@example.com',
            first_name='Dr. John',
            last_name='Smith',
            user_type=User.UserType.GP,
            password='testpass123'
        )
        self.patient = User.objects.create_user(
            email='patient@example.com',
            first_name='Jane',
            last_name='Doe',
            user_type=User.UserType.PATIENT,
            password='testpass123'
        )
    
    def test_create_referral(self):
        """Test creating a referral."""
        referral = Referral.objects.create(
            referrer=self.referrer,
            patient=self.patient,
            presenting_problem='Anxiety and depression',
            clinical_notes='Patient reports symptoms for 6 months',
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.MIXED,
            priority=Referral.Priority.MEDIUM,
            max_distance_km=50,
            created_by=self.referrer
        )
        
        self.assertEqual(referral.referrer, self.referrer)
        self.assertEqual(referral.patient, self.patient)
        self.assertEqual(referral.presenting_problem, 'Anxiety and depression')
        self.assertEqual(referral.service_type, Referral.ServiceType.NHS)
        self.assertEqual(referral.status, Referral.Status.DRAFT)
        self.assertTrue(referral.referral_id)
    
    def test_referral_str_representation(self):
        """Test referral string representation."""
        referral = Referral.objects.create(
            referrer=self.referrer,
            patient=self.patient,
            presenting_problem='Test problem',
            created_by=self.referrer
        )
        expected = f"Referral {referral.referral_id} - {self.patient.get_full_name()}"
        self.assertEqual(str(referral), expected)
    
    def test_referral_status_properties(self):
        """Test referral status properties."""
        referral = Referral.objects.create(
            referrer=self.referrer,
            patient=self.patient,
            presenting_problem='Test problem',
            created_by=self.referrer
        )
        
        self.assertTrue(referral.is_draft)
        self.assertFalse(referral.is_submitted)
        self.assertFalse(referral.is_matching)
        self.assertFalse(referral.is_completed)
        
        referral.status = Referral.Status.SUBMITTED
        referral.save()
        
        self.assertFalse(referral.is_draft)
        self.assertTrue(referral.is_submitted)


class CandidateModelTest(TestCase):
    """
    Test cases for Candidate model.
    """
    
    def setUp(self):
        self.referrer = User.objects.create_user(
            email='referrer@example.com',
            first_name='Dr. John',
            last_name='Smith',
            user_type=User.UserType.GP,
            password='testpass123'
        )
        self.patient = User.objects.create_user(
            email='patient@example.com',
            first_name='Jane',
            last_name='Doe',
            user_type=User.UserType.PATIENT,
            password='testpass123'
        )
        self.psychologist = User.objects.create_user(
            email='psychologist@example.com',
            first_name='Dr. Sarah',
            last_name='Johnson',
            user_type=User.UserType.PSYCHOLOGIST,
            password='testpass123'
        )
        self.referral = Referral.objects.create(
            referrer=self.referrer,
            patient=self.patient,
            presenting_problem='Test problem',
            created_by=self.referrer
        )
    
    def test_create_candidate(self):
        """Test creating a candidate."""
        candidate = Candidate.objects.create(
            referral=self.referral,
            psychologist=self.psychologist,
            similarity_score=0.85,
            structured_score=0.90,
            final_score=0.87,
            confidence_score=0.82
        )
        
        self.assertEqual(candidate.referral, self.referral)
        self.assertEqual(candidate.psychologist, self.psychologist)
        self.assertEqual(candidate.similarity_score, 0.85)
        self.assertEqual(candidate.status, Candidate.Status.PENDING)
    
    def test_candidate_str_representation(self):
        """Test candidate string representation."""
        candidate = Candidate.objects.create(
            referral=self.referral,
            psychologist=self.psychologist
        )
        expected = f"Candidate {self.psychologist.get_full_name()} for {self.referral.referral_id}"
        self.assertEqual(str(candidate), expected)


class ReferralViewsTest(TestCase):
    """
    Test cases for referral views.
    """
    
    def setUp(self):
        self.client = Client()
        self.referrer = User.objects.create_user(
            email='referrer@example.com',
            first_name='Dr. John',
            last_name='Smith',
            user_type=User.UserType.GP,
            password='testpass123'
        )
        self.patient = User.objects.create_user(
            email='patient@example.com',
            first_name='Jane',
            last_name='Doe',
            user_type=User.UserType.PATIENT,
            password='testpass123'
        )
    
    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user."""
        self.client.login(email='referrer@example.com', password='testpass123')
        response = self.client.get(reverse('referrals:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view for unauthenticated user."""
        response = self.client.get(reverse('referrals:dashboard'))
        self.assertRedirects(response, f"{reverse('accounts:signin')}?next={reverse('referrals:dashboard')}")
    
    def test_create_referral_view_get(self):
        """Test create referral view GET request."""
        self.client.login(email='referrer@example.com', password='testpass123')
        response = self.client.get(reverse('referrals:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Referral')
    
    def test_create_referral_view_post(self):
        """Test create referral view POST request."""
        # Create a patient for the referral
        patient = User.objects.create_user(
            email='patient@example.com',
            password='testpass123',
            first_name='Patient',
            last_name='User',
            user_type=User.UserType.PATIENT
        )
        
        self.client.login(email='referrer@example.com', password='testpass123')
        response = self.client.post(reverse('referrals:create'), {
            'patient': patient.id,
            'presenting_problem': 'Test anxiety',
            'clinical_notes': 'Patient reports symptoms',
            'service_type': Referral.ServiceType.NHS,
            'modality': Referral.Modality.MIXED,
            'priority': Referral.Priority.MEDIUM,
            'max_distance_km': 50
        })
        # Check that a referral was created
        self.assertEqual(Referral.objects.count(), 1)
        referral = Referral.objects.first()
        self.assertIsNotNone(referral)
        self.assertRedirects(response, reverse('referrals:referral_detail', kwargs={'pk': referral.pk}))


class ReferralAPITest(APITestCase):
    """
    Test cases for referral API views.
    """
    
    def setUp(self):
        self.referrer = User.objects.create_user(
            email='referrer@example.com',
            first_name='Dr. John',
            last_name='Smith',
            user_type=User.UserType.GP,
            password='testpass123'
        )
        self.patient = User.objects.create_user(
            email='patient@example.com',
            first_name='Jane',
            last_name='Doe',
            user_type=User.UserType.PATIENT,
            password='testpass123'
        )
        self.referral = Referral.objects.create(
            referrer=self.referrer,
            patient=self.patient,
            presenting_problem='Test problem',
            created_by=self.referrer
        )
    
    def test_referral_list_api_authenticated(self):
        """Test referral list API for authenticated user."""
        self.client.force_authenticate(user=self.referrer)
        response = self.client.get(reverse('referrals_api:referral-list'))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_referral_list_api_unauthenticated(self):
        """Test referral list API for unauthenticated user."""
        response = self.client.get(reverse('referrals_api:referral-list'))
        self.assertEqual(response.status_code, 403)
    
    def test_referral_detail_api(self):
        """Test referral detail API."""
        self.client.force_authenticate(user=self.referrer)
        response = self.client.get(reverse('referrals_api:referral-detail', kwargs={'id': self.referral.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['referral_id'], self.referral.referral_id)
    
    def test_submit_referral_api(self):
        """Test submit referral API."""
        self.client.force_authenticate(user=self.referrer)
        response = self.client.post(reverse('referrals_api:submit-referral', kwargs={'referral_id': self.referral.id}))
        self.assertEqual(response.status_code, 200)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.SUBMITTED)
    
    def test_submit_referral_api_invalid_status(self):
        """Test submit referral API with invalid status."""
        self.referral.status = Referral.Status.SUBMITTED
        self.referral.save()
        
        self.client.force_authenticate(user=self.referrer)
        response = self.client.post(reverse('referrals_api:submit-referral', kwargs={'referral_id': self.referral.id}))
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
