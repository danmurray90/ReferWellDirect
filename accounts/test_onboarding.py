"""
Tests for accounts app onboarding and verification functionality.
"""
import secrets
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import (
    Organisation,
    PatientClaimInvite,
    User,
    UserOrganisation,
    VerificationStatus,
)
from referrals.models import PatientProfile, Referral

User = get_user_model()


class GPOnboardingTestCase(TestCase):
    """Test cases for GP onboarding flow."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.gp_signup_url = reverse("accounts:gp_onboarding_start")

    def test_gp_signup_page_accessible(self):
        """Test that GP signup page is accessible."""
        response = self.client.get(self.gp_signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GP Registration")

    def test_gp_signup_redirects_authenticated_user(self):
        """Test that authenticated users are redirected."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", user_type=User.UserType.GP
        )
        self.client.login(email="test@example.com", password="testpass123")

        response = self.client.get(self.gp_signup_url)
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_gp_signup_creates_user_with_pending_verification(self):
        """Test that GP signup creates user with pending verification."""
        data = {
            "email": "gp@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+44123456789",
            "gmc_number": "12345678",
            "org_name": "Test Practice",
            "org_type": "gp_practice",
            "org_email": "practice@example.com",
            "org_phone": "+44123456790",
            "org_address": "123 Test Street",
            "org_city": "London",
            "org_postcode": "SW1A 1AA",
        }

        response = self.client.post(self.gp_signup_url, data)

        # Should redirect to verification pending page
        self.assertRedirects(response, reverse("accounts:verification_pending"))

        # Check user was created
        user = User.objects.get(email="gp@example.com")
        self.assertEqual(user.user_type, User.UserType.GP)
        self.assertFalse(user.is_verified)

        # Check verification status was created
        verification_status = VerificationStatus.objects.get(user=user)
        self.assertEqual(verification_status.status, VerificationStatus.Status.PENDING)

        # Check organisation was created
        organisation = Organisation.objects.get(name="Test Practice")
        self.assertEqual(
            organisation.organisation_type, Organisation.OrganisationType.GP_PRACTICE
        )

        # Check user-organisation link was created
        user_org = UserOrganisation.objects.get(user=user, organisation=organisation)
        self.assertEqual(user_org.role, UserOrganisation.Role.OWNER)

    def test_gp_signup_without_organisation(self):
        """Test GP signup without organisation details."""
        data = {
            "email": "gp@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+44123456789",
        }

        response = self.client.post(self.gp_signup_url, data)
        self.assertRedirects(response, reverse("accounts:verification_pending"))

        user = User.objects.get(email="gp@example.com")
        self.assertEqual(user.user_type, User.UserType.GP)

        # Should still create verification status
        verification_status = VerificationStatus.objects.get(user=user)
        self.assertEqual(verification_status.status, VerificationStatus.Status.PENDING)

    def test_gp_signup_validation_errors(self):
        """Test GP signup with validation errors."""
        data = {
            "email": "invalid-email",
            "password": "short",
            "first_name": "",
            "last_name": "",
        }

        response = self.client.post(self.gp_signup_url, data)
        self.assertEqual(response.status_code, 200)  # Should not redirect
        self.assertContains(response, "Please fill in all required fields")

    def test_gp_signup_duplicate_email(self):
        """Test GP signup with duplicate email."""
        User.objects.create_user(
            email="existing@example.com",
            password="testpass123",
            user_type=User.UserType.GP,
        )

        data = {
            "email": "existing@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
        }

        response = self.client.post(self.gp_signup_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Error creating account")


class PsychologistOnboardingTestCase(TestCase):
    """Test cases for Psychologist onboarding flow."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.psych_signup_url = reverse("accounts:psych_onboarding_start")

    def test_psych_signup_page_accessible(self):
        """Test that Psychologist signup page is accessible."""
        response = self.client.get(self.psych_signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Psychologist Registration")

    def test_psych_signup_creates_user_with_pending_verification(self):
        """Test that Psychologist signup creates user with pending verification."""
        data = {
            "email": "psych@example.com",
            "password": "testpass123",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+44123456789",
            "bio": "Experienced psychologist specializing in anxiety disorders",
            "specialisms": ["anxiety", "depression"],
            "modalities": ["cbt", "mindfulness"],
            "languages": ["en", "es"],
            "nhs_provider": "on",
            "address_line_1": "456 Therapy Lane",
            "city": "Manchester",
            "postcode": "M1 1AA",
        }

        response = self.client.post(self.psych_signup_url, data)

        # Should redirect to verification pending page
        self.assertRedirects(response, reverse("accounts:verification_pending"))

        # Check user was created
        user = User.objects.get(email="psych@example.com")
        self.assertEqual(user.user_type, User.UserType.PSYCHOLOGIST)
        self.assertFalse(user.is_verified)

        # Check verification status was created
        verification_status = VerificationStatus.objects.get(user=user)
        self.assertEqual(verification_status.status, VerificationStatus.Status.PENDING)

    def test_psych_signup_minimal_data(self):
        """Test Psychologist signup with minimal required data."""
        data = {
            "email": "psych@example.com",
            "password": "testpass123",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+44123456789",
        }

        response = self.client.post(self.psych_signup_url, data)
        self.assertRedirects(response, reverse("accounts:verification_pending"))

        user = User.objects.get(email="psych@example.com")
        self.assertEqual(user.user_type, User.UserType.PSYCHOLOGIST)

    def test_psych_wizard_two_step_redirects_to_details(self):
        """Starting wizard with flag should redirect to details step."""
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "wizard@example.com",
            "password": "testpass123",
            "start_wizard": "1",
        }
        response = self.client.post(self.psych_signup_url, data)
        self.assertRedirects(response, reverse("accounts:psych_onboarding_details"))

    def test_psych_details_requires_session(self):
        """Accessing details without step1 session should redirect to start."""
        response = self.client.get(reverse("accounts:psych_onboarding_details"))
        self.assertRedirects(response, self.psych_signup_url)

    def test_psych_details_completes_signup_and_creates_profile(self):
        """Posting details completes signup, creates user + psychologist profile."""
        # Seed session with step1 data
        session = self.client.session
        session["psych_signup_step1"] = {
            "first_name": "Wiz",
            "last_name": "Ard",
            "email": "wiz@example.com",
            "password": "testpass123",
            "phone": "+44123456789",
        }
        session.save()

        details = {
            "registration_body": "HCPC",
            "registration_number": "ABC123",
            "years_experience": 5,
            "bio": "Experienced clinician",
            "specialisms": "anxiety, depression",
            "languages": "en, es",
            "service_nhs": "on",
            "modality": "mixed",
            "address_line_1": "1 High St",
            "city": "London",
            "postcode": "SW1A 1AA",
            "max_patients": 80,
        }

        response = self.client.post(reverse("accounts:psych_onboarding_details"), details)
        # Should redirect to verification pending page
        self.assertRedirects(response, reverse("accounts:verification_pending"))

        # Verify user and profile creation
        user = User.objects.get(email="wiz@example.com")
        self.assertEqual(user.user_type, User.UserType.PSYCHOLOGIST)
        from catalogue.models import Psychologist

        profile = Psychologist.objects.get(user=user)
        self.assertEqual(profile.registration_body, "HCPC")
        self.assertEqual(profile.registration_number, "ABC123")


class VerificationSystemTestCase(TestCase):
    """Test cases for verification system."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            user_type=User.UserType.ADMIN,
            is_verified=True,
        )

        self.gp_user = User.objects.create_user(
            email="gp@example.com",
            password="gppass123",
            user_type=User.UserType.GP,
            is_verified=False,
        )

        self.verification_status = VerificationStatus.objects.create(
            user=self.gp_user, status=VerificationStatus.Status.PENDING
        )

    def test_verification_pending_page_accessible(self):
        """Test that verification pending page is accessible."""
        self.client.login(email="gp@example.com", password="gppass123")
        response = self.client.get(reverse("accounts:verification_pending"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verification Pending")

    def test_verification_pending_redirects_verified_user(self):
        """Test that verified users are redirected from verification pending page."""
        self.gp_user.is_verified = True
        self.gp_user.save()

        # Also update the verification status
        self.verification_status.status = VerificationStatus.Status.VERIFIED
        self.verification_status.vetted_by = self.admin_user
        self.verification_status.vetted_at = timezone.now()
        self.verification_status.save()

        self.client.login(email="gp@example.com", password="gppass123")
        response = self.client.get(reverse("accounts:verification_pending"))
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_admin_can_verify_user(self):
        """Test that admin can verify a user."""
        self.client.login(email="admin@example.com", password="adminpass123")

        # Verify the user
        self.verification_status.verify(self.admin_user, "Credentials verified")

        # Check verification status
        self.verification_status.refresh_from_db()
        self.assertEqual(
            self.verification_status.status, VerificationStatus.Status.VERIFIED
        )
        self.assertEqual(self.verification_status.vetted_by, self.admin_user)
        self.assertIsNotNone(self.verification_status.vetted_at)

    def test_admin_can_reject_user(self):
        """Test that admin can reject a user."""
        self.client.login(email="admin@example.com", password="adminpass123")

        # Reject the user
        self.verification_status.reject(self.admin_user, "Insufficient credentials")

        # Check verification status
        self.verification_status.refresh_from_db()
        self.assertEqual(
            self.verification_status.status, VerificationStatus.Status.REJECTED
        )
        self.assertEqual(self.verification_status.vetted_by, self.admin_user)
        self.assertIsNotNone(self.verification_status.vetted_at)


class PatientManagementTestCase(TestCase):
    """Test cases for patient management system."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.gp_user = User.objects.create_user(
            email="gp@example.com",
            password="gppass123",
            user_type=User.UserType.GP,
            is_verified=True,
        )

        # Create verification status
        VerificationStatus.objects.create(
            user=self.gp_user, status=VerificationStatus.Status.VERIFIED
        )

    def test_gp_create_patient_page_accessible(self):
        """Test that GP can access patient creation page."""
        self.client.login(email="gp@example.com", password="gppass123")
        response = self.client.get(reverse("accounts:gp_create_patient"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Patient Profile")

    def test_gp_create_patient_requires_verification(self):
        """Test that unverified GPs cannot create patients."""
        unverified_gp = User.objects.create_user(
            email="unverified@example.com",
            password="gppass123",
            user_type=User.UserType.GP,
            is_verified=False,
        )

        VerificationStatus.objects.create(
            user=unverified_gp, status=VerificationStatus.Status.PENDING
        )

        self.client.login(email="unverified@example.com", password="gppass123")
        response = self.client.get(reverse("accounts:gp_create_patient"))
        self.assertRedirects(response, reverse("accounts:verification_pending"))

    def test_gp_can_create_patient_profile(self):
        """Test that verified GP can create patient profile."""
        self.client.login(email="gp@example.com", password="gppass123")

        data = {
            "first_name": "Patient",
            "last_name": "Test",
            "email": "patient@example.com",
            "phone": "+44123456789",
            "date_of_birth": "1990-01-01",
            "nhs_number": "1234567890",
        }

        response = self.client.post(reverse("accounts:gp_create_patient"), data)

        # Should redirect to success page or dashboard
        self.assertEqual(response.status_code, 302)

        # Check patient profile was created
        patient_profile = PatientProfile.objects.get(email="patient@example.com")
        self.assertEqual(patient_profile.first_name, "Patient")
        self.assertEqual(patient_profile.last_name, "Test")
        self.assertEqual(patient_profile.created_by, self.gp_user)

    def test_gp_can_generate_patient_invite(self):
        """Test that GP can generate patient invite."""
        # Create a patient profile first
        patient_profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            created_by=self.gp_user,
        )

        self.client.login(email="gp@example.com", password="gppass123")

        data = {
            "email": "patient@example.com",
        }

        response = self.client.post(
            reverse(
                "accounts:gp_invite_patient", kwargs={"patient_id": patient_profile.id}
            ),
            data,
        )

        # Should render success page (200) not redirect
        self.assertEqual(response.status_code, 200)

        # Check invite was created
        invite = PatientClaimInvite.objects.get(patient_profile=patient_profile)
        self.assertEqual(invite.email, "patient@example.com")
        self.assertIsNotNone(invite.token)
        self.assertIsNotNone(invite.expires_at)

    def test_patient_invite_token_security(self):
        """Test that patient invite tokens are secure."""
        patient_profile = PatientProfile.objects.create(
            first_name="Patient",
            last_name="Test",
            email="patient@example.com",
            created_by=self.gp_user,
        )

        self.client.login(email="gp@example.com", password="gppass123")

        data = {"email": "patient@example.com"}
        response = self.client.post(
            reverse(
                "accounts:gp_invite_patient", kwargs={"patient_id": patient_profile.id}
            ),
            data,
        )

        invite = PatientClaimInvite.objects.get(patient_profile=patient_profile)

        # Token should be long and random
        self.assertGreaterEqual(len(invite.token), 32)

        # Token should be different each time - create another invite
        response2 = self.client.post(
            reverse(
                "accounts:gp_invite_patient", kwargs={"patient_id": patient_profile.id}
            ),
            data,
        )

        # Get the most recent invite (there should be 2 now)
        invites = PatientClaimInvite.objects.filter(
            patient_profile=patient_profile
        ).order_by("-created_at")
        self.assertEqual(invites.count(), 2)
        invite2 = invites.first()  # Most recent
        self.assertNotEqual(invite.token, invite2.token)


class PatientClaimTestCase(TestCase):
    """Test cases for patient claim flow."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
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

        self.invite = PatientClaimInvite.objects.create(
            token="test-token-123",
            patient_profile=self.patient_profile,
            email="patient@example.com",
            expires_at=timezone.now() + timezone.timedelta(days=7),
            created_by=self.gp_user,
        )

    def test_patient_claim_page_accessible(self):
        """Test that patient claim page is accessible with valid token."""
        response = self.client.get(
            reverse("accounts:patient_claim", kwargs={"token": "test-token-123"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Claim Your Profile")

    def test_patient_claim_invalid_token(self):
        """Test that invalid token redirects to landing page."""
        response = self.client.get(
            reverse("accounts:patient_claim", kwargs={"token": "invalid-token"})
        )
        self.assertRedirects(response, reverse("public:landing"))

    def test_patient_claim_expired_token(self):
        """Test that expired token is rejected."""
        self.invite.expires_at = timezone.now() - timezone.timedelta(days=1)
        self.invite.save()

        response = self.client.get(
            reverse("accounts:patient_claim", kwargs={"token": "test-token-123"})
        )
        self.assertRedirects(response, reverse("public:landing"))

    def test_patient_claim_used_token(self):
        """Test that used token is rejected."""
        self.invite.used_at = timezone.now()
        self.invite.save()

        response = self.client.get(
            reverse("accounts:patient_claim", kwargs={"token": "test-token-123"})
        )
        self.assertRedirects(response, reverse("public:landing"))

    def test_patient_claim_creates_user_and_links_profile(self):
        """Test that patient claim creates user and links profile."""
        data = {
            "email": "patient@example.com",
            "password": "patientpass123",
            "first_name": "Patient",
            "last_name": "Test",
        }

        response = self.client.post(
            reverse("accounts:patient_claim", kwargs={"token": "test-token-123"}), data
        )

        # Should redirect to dashboard
        self.assertRedirects(response, reverse("accounts:dashboard"))

        # Check user was created
        user = User.objects.get(email="patient@example.com")
        self.assertEqual(user.user_type, User.UserType.PATIENT)
        self.assertTrue(user.is_verified)  # Patients don't need verification

        # Check profile was linked
        self.patient_profile.refresh_from_db()
        self.assertEqual(self.patient_profile.user, user)

        # Check invite was marked as used
        self.invite.refresh_from_db()
        self.assertIsNotNone(self.invite.used_at)

    def test_patient_claim_validation_errors(self):
        """Test patient claim with validation errors."""
        data = {
            "email": "invalid-email",
            "password": "short",
            "first_name": "",
            "last_name": "",
        }

        response = self.client.post(
            reverse("accounts:patient_claim", kwargs={"token": "test-token-123"}), data
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please fill in all required fields")
