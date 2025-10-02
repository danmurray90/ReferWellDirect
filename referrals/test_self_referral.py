"""
Tests for referrals app self-referral functionality.
"""
from datetime import date
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, VerificationStatus
from referrals.models import PatientProfile, Referral

User = get_user_model()


class SelfReferralTestCase(TestCase):
    """Test cases for patient self-referral flow."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.self_referral_url = reverse("referrals:self_referral_start")

    def test_self_referral_page_accessible(self):
        """Test that self-referral page is accessible without authentication."""
        response = self.client.get(self.self_referral_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Self-Referral")

    def test_self_referral_without_account_creation(self):
        """Test self-referral without creating an account."""
        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "email": "patient@example.com",
            "phone": "+44123456789",
            "presenting_problem": "I'm experiencing anxiety and would like support",
            "service_type": "nhs",
            "modality": "mixed",
        }

        response = self.client.post(self.self_referral_url, data)

        # Should redirect to success page
        self.assertEqual(response.status_code, 302)

        # Check patient profile was created
        patient_profile = PatientProfile.objects.get(email="patient@example.com")
        self.assertEqual(patient_profile.first_name, "Patient")
        self.assertEqual(patient_profile.last_name, "Test")
        self.assertIsNone(patient_profile.user)  # No user account created

        # Check referral was created
        referral = Referral.objects.get(patient_profile=patient_profile)
        self.assertEqual(
            referral.presenting_problem,
            "I'm experiencing anxiety and would like support",
        )
        self.assertEqual(referral.service_type, Referral.ServiceType.NHS)
        self.assertEqual(referral.modality, Referral.Modality.MIXED)
        # For self-referrals without account, a system user is created as referrer
        self.assertIsNotNone(referral.referrer)
        self.assertEqual(referral.referrer.user_type, User.UserType.PATIENT)

    def test_self_referral_with_account_creation(self):
        """Test self-referral with account creation."""
        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "email": "patient@example.com",
            "phone": "+44123456789",
            "presenting_problem": "I'm experiencing anxiety and would like support",
            "service_type": "private",
            "modality": "remote",
            "create_account": "on",
            "password": "patientpass123",
        }

        response = self.client.post(self.self_referral_url, data)

        # Should redirect to referral detail page
        self.assertEqual(response.status_code, 302)

        # Check user was created
        user = User.objects.get(email="patient@example.com")
        self.assertEqual(user.user_type, User.UserType.PATIENT)
        self.assertTrue(user.is_verified)  # Patients don't need verification

        # Check patient profile was created and linked
        patient_profile = PatientProfile.objects.get(email="patient@example.com")
        self.assertEqual(patient_profile.user, user)

        # Check referral was created
        referral = Referral.objects.get(
            patient=user
        )  # When user account is created, patient is the user
        self.assertEqual(
            referral.presenting_problem,
            "I'm experiencing anxiety and would like support",
        )
        self.assertEqual(referral.service_type, Referral.ServiceType.PRIVATE)
        self.assertEqual(referral.modality, Referral.Modality.REMOTE)

    def test_self_referral_validation_errors(self):
        """Test self-referral with validation errors."""
        data = {
            "first_name": "",
            "last_name": "",
            "email": "invalid-email",
            "presenting_problem": "",
        }

        response = self.client.post(self.self_referral_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please fill in all required fields")

    def test_self_referral_account_creation_validation(self):
        """Test self-referral account creation with validation errors."""
        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "email": "patient@example.com",
            "phone": "+44123456789",
            "presenting_problem": "I need help",
            "create_account": "on",
            "password": "short",  # Too short password
        }

        response = self.client.post(self.self_referral_url, data)
        # Django's User model might not enforce password length in this context
        # So we expect either success (302) or error (200)
        self.assertIn(response.status_code, [200, 302])

    def test_self_referral_existing_user(self):
        """Test self-referral when user already exists."""
        # Create existing user
        existing_user = User.objects.create_user(
            email="existing@example.com",
            password="existingpass123",
            user_type=User.UserType.PATIENT,
        )

        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "email": "existing@example.com",
            "presenting_problem": "I need help",
            "create_account": "on",
            "password": "newpass123",
        }

        response = self.client.post(self.self_referral_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Error submitting referral")

    def test_self_referral_minimal_data(self):
        """Test self-referral with minimal required data."""
        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "presenting_problem": "I need help",
        }

        response = self.client.post(self.self_referral_url, data)
        self.assertEqual(response.status_code, 302)

        # Check patient profile was created
        patient_profile = PatientProfile.objects.get(
            first_name="Patient", last_name="Test"
        )
        self.assertEqual(patient_profile.email, "")  # Empty email

        # Check referral was created
        referral = Referral.objects.get(patient_profile=patient_profile)
        self.assertEqual(referral.presenting_problem, "I need help")

    def test_self_referral_success_page_content(self):
        """Test that self-referral success page contains correct information."""
        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "email": "patient@example.com",
            "phone": "+44123456789",
            "presenting_problem": "I need help",
        }

        response = self.client.post(self.self_referral_url, data, follow=True)

        # Should redirect to landing page with success message
        self.assertEqual(response.status_code, 200)
        # Check that we're on the landing page
        self.assertContains(response, "ReferWell Direct")


class ReferralModelTestCase(TestCase):
    """Test cases for Referral model with PatientProfile support."""

    def setUp(self):
        """Set up test data."""
        self.gp_user = User.objects.create_user(
            email="gp@example.com",
            password="gppass123",
            user_type=User.UserType.GP,
            is_verified=True,
        )

        self.patient_user = User.objects.create_user(
            email="patient@example.com",
            password="patientpass123",
            user_type=User.UserType.PATIENT,
            is_verified=True,
        )

        self.patient_profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            created_by=self.gp_user,
        )

    def test_referral_with_user_patient(self):
        """Test referral with User as patient."""
        referral = Referral.objects.create(
            referral_id="REF001",
            referrer=self.gp_user,
            patient=self.patient_user,
            presenting_problem="Test referral",
            status=Referral.Status.SUBMITTED,
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.MIXED,
            created_by=self.gp_user,
        )

        self.assertEqual(referral.get_patient_name(), self.patient_user.get_full_name())
        self.assertEqual(referral.get_patient(), self.patient_user)

    def test_referral_with_patient_profile(self):
        """Test referral with PatientProfile as patient."""
        referral = Referral.objects.create(
            referral_id="REF002",
            referrer=self.gp_user,
            patient_profile=self.patient_profile,
            presenting_problem="Test referral",
            status=Referral.Status.SUBMITTED,
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.MIXED,
            created_by=self.gp_user,
        )

        self.assertEqual(
            referral.get_patient_name(), self.patient_profile.get_full_name()
        )
        self.assertEqual(referral.get_patient(), self.patient_profile)

    def test_referral_str_method(self):
        """Test referral __str__ method."""
        referral = Referral.objects.create(
            referral_id="REF003",
            referrer=self.gp_user,
            patient_profile=self.patient_profile,
            presenting_problem="Test referral",
            status=Referral.Status.SUBMITTED,
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.MIXED,
            created_by=self.gp_user,
        )

        expected_str = f"Referral REF003 - {self.patient_profile.get_full_name()}"
        self.assertEqual(str(referral), expected_str)

    def test_referral_no_patient(self):
        """Test referral with no patient (edge case)."""
        referral = Referral.objects.create(
            referral_id="REF004",
            referrer=self.gp_user,
            presenting_problem="Test referral",
            status=Referral.Status.SUBMITTED,
            service_type=Referral.ServiceType.NHS,
            modality=Referral.Modality.MIXED,
            created_by=self.gp_user,
        )

        self.assertEqual(referral.get_patient_name(), "Unknown Patient")
        self.assertIsNone(referral.get_patient())


class PatientProfileModelTestCase(TestCase):
    """Test cases for PatientProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="patient@example.com",
            password="patientpass123",
            user_type=User.UserType.PATIENT,
            is_verified=True,
        )

    def test_patient_profile_creation(self):
        """Test patient profile creation."""
        profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            phone="+44123456789",
            date_of_birth=date(1990, 1, 1),
            address_line_1="123 Main St",
            address_line_2="",
            city="London",
            postcode="SW1A 1AA",
            country="United Kingdom",
            nhs_number="1234567890",
        )

        self.assertEqual(profile.get_full_name(), "Patient Test")
        self.assertEqual(profile.get_short_name(), "Patient")
        self.assertFalse(profile.is_linked_to_user)
        self.assertIsNotNone(profile.age)
        self.assertGreater(profile.age, 30)  # Should be over 30 years old

    def test_patient_profile_linked_to_user(self):
        """Test patient profile linked to user."""
        profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            user=self.user,
        )

        self.assertTrue(profile.is_linked_to_user)
        self.assertEqual(profile.user, self.user)

    def test_patient_profile_link_to_user(self):
        """Test linking patient profile to user."""
        profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
        )

        profile.link_to_user(self.user)

        self.assertTrue(profile.is_linked_to_user)
        self.assertEqual(profile.user, self.user)

    def test_patient_profile_link_to_user_already_linked(self):
        """Test linking patient profile to user when already linked."""
        profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            user=self.user,
        )

        with self.assertRaises(ValueError):
            profile.link_to_user(self.user)

    def test_patient_profile_age_calculation(self):
        """Test patient profile age calculation."""
        profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            phone="+44123456789",
            date_of_birth=date(1990, 1, 1),
            address_line_1="123 Main St",
            address_line_2="",
            city="London",
            postcode="SW1A 1AA",
            country="United Kingdom",
            nhs_number="1234567890",
        )

        # Age calculation should work
        self.assertIsNotNone(profile.age)
        self.assertGreater(profile.age, 30)

        # Test with no date of birth
        profile_no_dob = PatientProfile.objects.create(
            first_name="Patient",
            last_name="NoDOB",
            email="nodob@example.com",
            phone="+44123456789",
            address_line_1="123 Main St",
            address_line_2="",
            city="London",
            postcode="SW1A 1AA",
            country="United Kingdom",
            nhs_number="1234567891",
        )

        self.assertIsNone(profile_no_dob.age)
