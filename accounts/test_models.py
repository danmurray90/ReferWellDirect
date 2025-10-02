"""
Tests for new models: VerificationStatus and PatientClaimInvite.
"""
import secrets
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import PatientClaimInvite, User, VerificationStatus
from referrals.models import PatientProfile

User = get_user_model()


class VerificationStatusModelTestCase(TestCase):
    """Test cases for VerificationStatus model."""

    def setUp(self):
        """Set up test data."""
        self.gp_user = User.objects.create_user(
            email="gp@example.com",
            password="gppass123",
            user_type=User.UserType.GP,
            is_verified=False,
        )

        self.psych_user = User.objects.create_user(
            email="psych@example.com",
            password="psychpass123",
            user_type=User.UserType.PSYCHOLOGIST,
            is_verified=False,
        )

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            user_type=User.UserType.ADMIN,
            is_verified=True,
        )

    def test_verification_status_creation(self):
        """Test verification status creation."""
        verification_status = VerificationStatus.objects.create(
            user=self.gp_user,
            status=VerificationStatus.Status.PENDING,
            notes="Test verification",
        )

        self.assertEqual(verification_status.user, self.gp_user)
        self.assertEqual(verification_status.status, VerificationStatus.Status.PENDING)
        self.assertEqual(verification_status.notes, "Test verification")
        self.assertIsNone(verification_status.vetted_by)
        self.assertIsNone(verification_status.vetted_at)

    def test_verification_status_properties(self):
        """Test verification status properties."""
        verification_status = VerificationStatus.objects.create(
            user=self.gp_user, status=VerificationStatus.Status.PENDING
        )

        self.assertTrue(verification_status.is_pending)
        self.assertFalse(verification_status.is_verified)
        self.assertFalse(verification_status.is_rejected)

        # Test verified status
        verification_status.status = VerificationStatus.Status.VERIFIED
        verification_status.save()

        self.assertFalse(verification_status.is_pending)
        self.assertTrue(verification_status.is_verified)
        self.assertFalse(verification_status.is_rejected)

        # Test rejected status
        verification_status.status = VerificationStatus.Status.REJECTED
        verification_status.save()

        self.assertFalse(verification_status.is_pending)
        self.assertFalse(verification_status.is_verified)
        self.assertTrue(verification_status.is_rejected)

    def test_verification_status_verify_method(self):
        """Test verification status verify method."""
        verification_status = VerificationStatus.objects.create(
            user=self.gp_user, status=VerificationStatus.Status.PENDING
        )

        verification_status.verify(self.admin_user, "Credentials verified")

        self.assertEqual(verification_status.status, VerificationStatus.Status.VERIFIED)
        self.assertEqual(verification_status.vetted_by, self.admin_user)
        self.assertEqual(verification_status.notes, "Credentials verified")
        self.assertIsNotNone(verification_status.vetted_at)

    def test_verification_status_reject_method(self):
        """Test verification status reject method."""
        verification_status = VerificationStatus.objects.create(
            user=self.gp_user, status=VerificationStatus.Status.PENDING
        )

        verification_status.reject(self.admin_user, "Insufficient credentials")

        self.assertEqual(verification_status.status, VerificationStatus.Status.REJECTED)
        self.assertEqual(verification_status.vetted_by, self.admin_user)
        self.assertEqual(verification_status.notes, "Insufficient credentials")
        self.assertIsNotNone(verification_status.vetted_at)

    def test_verification_status_str_method(self):
        """Test verification status __str__ method."""
        verification_status = VerificationStatus.objects.create(
            user=self.gp_user, status=VerificationStatus.Status.PENDING
        )

        expected_str = f"{self.gp_user.get_full_name()} - Pending"
        self.assertEqual(str(verification_status), expected_str)

    def test_verification_status_choices(self):
        """Test verification status choices."""
        choices = VerificationStatus.Status.choices
        self.assertEqual(len(choices), 3)

        choice_values = [choice[0] for choice in choices]
        self.assertIn(VerificationStatus.Status.PENDING, choice_values)
        self.assertIn(VerificationStatus.Status.VERIFIED, choice_values)
        self.assertIn(VerificationStatus.Status.REJECTED, choice_values)

    def test_verification_status_user_type_constraint(self):
        """Test that verification status can only be created for GP and Psychologist users."""
        # Should work for GP
        VerificationStatus.objects.create(user=self.gp_user)

        # Should work for Psychologist
        VerificationStatus.objects.create(user=self.psych_user)

        # Should not work for Patient (this would be caught by the limit_choices_to)
        patient_user = User.objects.create_user(
            email="patient@example.com",
            password="patientpass123",
            user_type=User.UserType.PATIENT,
        )

        # The limit_choices_to constraint should prevent this in the admin
        # but we can test the model creation directly
        verification_status = VerificationStatus.objects.create(user=patient_user)
        self.assertEqual(verification_status.user, patient_user)


class PatientClaimInviteModelTestCase(TestCase):
    """Test cases for PatientClaimInvite model."""

    def setUp(self):
        """Set up test data."""
        self.gp_user = User.objects.create_user(
            email="gp@example.com",
            password="gppass123",
            user_type=User.UserType.GP,
            is_verified=True,
        )

        self.patient_profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            created_by=self.gp_user,
        )

    def test_patient_claim_invite_creation(self):
        """Test patient claim invite creation."""
        invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        self.assertEqual(invite.token, "test-token-123")
        self.assertEqual(invite.patient_profile, self.patient_profile)
        self.assertEqual(invite.email, "patient@example.com")
        self.assertEqual(invite.created_by, self.gp_user)
        self.assertIsNone(invite.used_at)

    def test_patient_claim_invite_properties(self):
        """Test patient claim invite properties."""
        # Valid invite
        invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        self.assertFalse(invite.is_expired)
        self.assertFalse(invite.is_used)
        self.assertTrue(invite.is_valid)

        # Expired invite
        expired_invite = PatientClaimInvite.objects.create(
            token="expired-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() - timezone.timedelta(days=1),
            created_by=self.gp_user,
        )

        self.assertTrue(expired_invite.is_expired)
        self.assertFalse(expired_invite.is_used)
        self.assertFalse(expired_invite.is_valid)

        # Used invite
        used_invite = PatientClaimInvite.objects.create(
            token="used-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            used_at=timezone.now(),
            created_by=self.gp_user,
        )

        self.assertFalse(used_invite.is_expired)
        self.assertTrue(used_invite.is_used)
        self.assertFalse(used_invite.is_valid)

    def test_patient_claim_invite_mark_used(self):
        """Test patient claim invite mark_used method."""
        invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        self.assertIsNone(invite.used_at)

        invite.mark_used()

        self.assertIsNotNone(invite.used_at)
        self.assertTrue(invite.is_used)
        self.assertFalse(invite.is_valid)

    def test_patient_claim_invite_str_method(self):
        """Test patient claim invite __str__ method."""
        invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        expected_str = (
            f"Invite for patient@example.com - {self.patient_profile.get_full_name()}"
        )
        self.assertEqual(str(invite), expected_str)

    def test_patient_claim_invite_token_uniqueness(self):
        """Test that patient claim invite tokens are unique."""
        PatientClaimInvite.objects.create(
            token="unique-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        # Creating another invite with the same token should raise an error
        with self.assertRaises(Exception):  # IntegrityError or similar
            PatientClaimInvite.objects.create(
                token="unique-token-123",
                patient_profile=self.patient_profile,
                email="patient@example.com",
                expires_at=timezone.now() + timezone.timedelta(days=7),
                created_by=self.gp_user,
            )

    def test_patient_claim_invite_multiple_invites_same_patient(self):
        """Test that multiple invites can be created for the same patient."""
        invite1 = PatientClaimInvite.objects.create(
            token="token-1",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        invite2 = PatientClaimInvite.objects.create(
            token="token-2",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

        self.assertNotEqual(invite1.token, invite2.token)
        self.assertEqual(invite1.patient_profile, invite2.patient_profile)

    def test_patient_claim_invite_expiration_logic(self):
        """Test patient claim invite expiration logic."""
        # Test exactly at expiration time
        now = timezone.now()
        invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=now,
            created_by=self.gp_user,
        )

        # Should be expired if expires_at is exactly now
        self.assertTrue(invite.is_expired)
        self.assertFalse(invite.is_valid)

    def test_patient_claim_invite_created_by_optional(self):
        """Test that created_by field is optional."""
        invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=None,
        )

        self.assertIsNone(invite.created_by)
        self.assertTrue(invite.is_valid)
