"""
Tests for catalogue app.
"""
import json

from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import Client, TestCase
from django.urls import reverse

from .models import Availability, Psychologist, Qualification, Review, Specialism

User = get_user_model()


class PsychologistModelTest(TestCase):
    """
    Test cases for Psychologist model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="psychologist@example.com",
            first_name="Dr. Sarah",
            last_name="Johnson",
            user_type=User.UserType.PSYCHOLOGIST,
            password="testpass123",
        )

    def test_create_psychologist(self):
        """Test creating a psychologist."""
        psychologist = Psychologist.objects.create(
            user=self.user,
            title="Dr.",
            qualifications=["DClinPsy", "BSc Psychology"],
            specialisms=["Anxiety", "Depression"],
            languages=["en", "es"],
            service_type=Psychologist.ServiceType.MIXED,
            modality=Psychologist.Modality.MIXED,
            registration_number="HCPC123456",
            registration_body="HCPC",
            years_experience=10,
            max_patients=50,
            current_patients=25,
        )

        self.assertEqual(psychologist.user, self.user)
        self.assertEqual(psychologist.title, "Dr.")
        self.assertEqual(psychologist.qualifications, ["DClinPsy", "BSc Psychology"])
        self.assertEqual(psychologist.specialisms, ["Anxiety", "Depression"])
        self.assertEqual(psychologist.service_type, Psychologist.ServiceType.MIXED)
        self.assertEqual(psychologist.registration_number, "HCPC123456")
        self.assertTrue(psychologist.capacity_available)
        self.assertTrue(psychologist.is_available)

    def test_psychologist_str_representation(self):
        """Test psychologist string representation."""
        psychologist = Psychologist.objects.create(
            user=self.user, service_type=Psychologist.ServiceType.NHS
        )
        expected = (
            f"{self.user.get_full_name()} - {psychologist.get_service_type_display()}"
        )
        self.assertEqual(str(psychologist), expected)

    def test_psychologist_capacity_available(self):
        """Test psychologist capacity availability."""
        psychologist = Psychologist.objects.create(
            user=self.user, max_patients=50, current_patients=25
        )

        self.assertTrue(psychologist.capacity_available)

        psychologist.current_patients = 50
        psychologist.save()

        self.assertFalse(psychologist.capacity_available)

    def test_psychologist_is_available(self):
        """Test psychologist availability status."""
        psychologist = Psychologist.objects.create(
            user=self.user,
            availability_status=Psychologist.AvailabilityStatus.AVAILABLE,
            is_active=True,
            is_accepting_referrals=True,
            max_patients=50,
            current_patients=25,
        )

        self.assertTrue(psychologist.is_available)

        psychologist.availability_status = Psychologist.AvailabilityStatus.BUSY
        psychologist.save()

        self.assertFalse(psychologist.is_available)


class AvailabilityModelTest(TestCase):
    """
    Test cases for Availability model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="psychologist@example.com",
            first_name="Dr. Sarah",
            last_name="Johnson",
            user_type=User.UserType.PSYCHOLOGIST,
            password="testpass123",
        )
        self.psychologist = Psychologist.objects.create(
            user=self.user, service_type=Psychologist.ServiceType.NHS
        )

    def test_create_availability(self):
        """Test creating availability."""
        availability = Availability.objects.create(
            psychologist=self.psychologist,
            day_of_week=Availability.DayOfWeek.MONDAY,
            start_time="09:00",
            end_time="17:00",
            modality=Psychologist.Modality.IN_PERSON,
        )

        self.assertEqual(availability.psychologist, self.psychologist)
        self.assertEqual(availability.day_of_week, Availability.DayOfWeek.MONDAY)
        self.assertEqual(availability.start_time, "09:00")
        self.assertEqual(availability.end_time, "17:00")
        self.assertEqual(availability.modality, Psychologist.Modality.IN_PERSON)
        self.assertTrue(availability.is_active)

    def test_availability_str_representation(self):
        """Test availability string representation."""
        availability = Availability.objects.create(
            psychologist=self.psychologist,
            day_of_week=Availability.DayOfWeek.MONDAY,
            start_time="09:00",
            end_time="17:00",
        )
        expected = f"{self.psychologist.user.get_full_name()} - Monday 09:00-17:00"
        self.assertEqual(str(availability), expected)


class SpecialismModelTest(TestCase):
    """
    Test cases for Specialism model.
    """

    def test_create_specialism(self):
        """Test creating specialism."""
        specialism = Specialism.objects.create(
            name="Anxiety Disorders",
            description="Treatment of various anxiety disorders",
            category="Anxiety",
        )

        self.assertEqual(specialism.name, "Anxiety Disorders")
        self.assertEqual(
            specialism.description, "Treatment of various anxiety disorders"
        )
        self.assertEqual(specialism.category, "Anxiety")
        self.assertTrue(specialism.is_active)

    def test_specialism_str_representation(self):
        """Test specialism string representation."""
        specialism = Specialism.objects.create(name="Depression")
        self.assertEqual(str(specialism), "Depression")


class ReviewModelTest(TestCase):
    """
    Test cases for Review model.
    """

    def setUp(self):
        self.psychologist_user = User.objects.create_user(
            email="psychologist@example.com",
            first_name="Dr. Sarah",
            last_name="Johnson",
            user_type=User.UserType.PSYCHOLOGIST,
            password="testpass123",
        )
        self.patient_user = User.objects.create_user(
            email="patient@example.com",
            first_name="Jane",
            last_name="Doe",
            user_type=User.UserType.PATIENT,
            password="testpass123",
        )
        self.psychologist = Psychologist.objects.create(
            user=self.psychologist_user, service_type=Psychologist.ServiceType.NHS
        )

    def test_create_review(self):
        """Test creating review."""
        review = Review.objects.create(
            psychologist=self.psychologist,
            patient=self.patient_user,
            rating=Review.Rating.FIVE,
            title="Excellent therapist",
            content="Very helpful and professional",
        )

        self.assertEqual(review.psychologist, self.psychologist)
        self.assertEqual(review.patient, self.patient_user)
        self.assertEqual(review.rating, Review.Rating.FIVE)
        self.assertEqual(review.title, "Excellent therapist")
        self.assertEqual(review.content, "Very helpful and professional")
        self.assertFalse(review.is_verified)
        self.assertTrue(review.is_public)

    def test_review_str_representation(self):
        """Test review string representation."""
        review = Review.objects.create(
            psychologist=self.psychologist,
            patient=self.patient_user,
            rating=Review.Rating.FIVE,
            title="Great therapist",
            content="Very helpful",
        )
        expected = f"Review of {self.psychologist.user.get_full_name()} by {self.patient_user.get_full_name()}"
        self.assertEqual(str(review), expected)


class PsychologistViewsTest(TestCase):
    """
    Test cases for psychologist views.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="psychologist@example.com",
            first_name="Dr. Sarah",
            last_name="Johnson",
            user_type=User.UserType.PSYCHOLOGIST,
            password="testpass123",
        )
        self.psychologist = Psychologist.objects.create(
            user=self.user, service_type=Psychologist.ServiceType.NHS
        )

    def test_psychologist_list_view_authenticated(self):
        """Test psychologist list view for authenticated user."""
        self.client.login(email="psychologist@example.com", password="testpass123")
        response = self.client.get(reverse("catalogue:psychologist_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Sarah Johnson")

    def test_psychologist_list_view_unauthenticated(self):
        """Test psychologist list view for unauthenticated user."""
        response = self.client.get(reverse("catalogue:psychologist_list"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:signin')}?next={reverse('catalogue:psychologist_list')}",
        )

    def test_psychologist_detail_view(self):
        """Test psychologist detail view."""
        self.client.login(email="psychologist@example.com", password="testpass123")
        response = self.client.get(
            reverse(
                "catalogue:psychologist_detail", kwargs={"pk": self.psychologist.pk}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Sarah Johnson")

    def test_psychologist_dashboard_view(self):
        """Test psychologist dashboard view."""
        self.client.login(email="psychologist@example.com", password="testpass123")
        response = self.client.get(reverse("catalogue:psychologist_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Sarah Johnson")


class PsychologistAPITest(APITestCase):
    """
    Test cases for psychologist API views.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="psychologist@example.com",
            first_name="Dr. Sarah",
            last_name="Johnson",
            user_type=User.UserType.PSYCHOLOGIST,
            password="testpass123",
        )
        self.psychologist = Psychologist.objects.create(
            user=self.user, service_type=Psychologist.ServiceType.NHS
        )

    def test_psychologist_list_api_authenticated(self):
        """Test psychologist list API for authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("catalogue_api:psychologist-list"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_psychologist_list_api_unauthenticated(self):
        """Test psychologist list API for unauthenticated user."""
        response = self.client.get(reverse("catalogue_api:psychologist-list"))
        self.assertEqual(response.status_code, 403)

    def test_psychologist_detail_api(self):
        """Test psychologist detail API."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                "catalogue_api:psychologist-detail", kwargs={"id": self.psychologist.id}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_name"], "Dr. Sarah Johnson")

    def test_update_psychologist_availability_api(self):
        """Test update psychologist availability API."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse(
                "catalogue_api:update-availability",
                kwargs={"psychologist_id": self.psychologist.id},
            ),
            {"availability_status": "busy", "is_accepting_referrals": False},
        )
        self.assertEqual(response.status_code, 200)
        self.psychologist.refresh_from_db()
        self.assertEqual(self.psychologist.availability_status, "busy")
        self.assertFalse(self.psychologist.is_accepting_referrals)
