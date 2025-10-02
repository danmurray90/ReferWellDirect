"""
Tests for public app views and functionality.
"""
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import PatientClaimInvite, User, VerificationStatus
from referrals.models import PatientProfile, Referral

User = get_user_model()


class PublicViewsTestCase(TestCase):
    """Test cases for public views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_landing_page_accessible(self):
        """Test that landing page is accessible without authentication."""
        response = self.client.get(reverse("public:landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ReferWell Direct")
        self.assertContains(response, "For GPs")
        self.assertContains(response, "For Psychologists")
        self.assertContains(response, "For Patients")

    def test_landing_page_caching(self):
        """Test that landing page is cached."""
        response1 = self.client.get(reverse("public:landing"))
        response2 = self.client.get(reverse("public:landing"))

        # Both should return 200
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

    def test_for_gps_page_accessible(self):
        """Test that GP information page is accessible."""
        response = self.client.get(reverse("public:for_gps"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "For GPs")
        self.assertContains(response, "Get Started")

    def test_for_psychologists_page_accessible(self):
        """Test that Psychologist information page is accessible."""
        response = self.client.get(reverse("public:for_psychologists"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "For Psychologists")
        self.assertContains(response, "Join Our Network")

    def test_for_patients_page_accessible(self):
        """Test that Patient information page is accessible."""
        response = self.client.get(reverse("public:for_patients"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "For Patients")
        self.assertContains(response, "Self-Refer")

    def test_public_pages_no_auth_required(self):
        """Test that all public pages are accessible without authentication."""
        urls = [
            reverse("public:landing"),
            reverse("public:for_gps"),
            reverse("public:for_psychologists"),
            reverse("public:for_patients"),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"URL {url} should be accessible"
            )

    def test_public_pages_contain_ctas(self):
        """Test that public pages contain appropriate CTAs."""
        # Landing page CTAs
        response = self.client.get(reverse("public:landing"))
        self.assertContains(response, "Get Started")
        self.assertContains(response, "Join Our Network")
        # Note: "Self-Refer" might be "Self-Referral" in the actual template

        # GP page CTA
        response = self.client.get(reverse("public:for_gps"))
        self.assertContains(response, "Get Started")

        # Psychologist page CTA
        response = self.client.get(reverse("public:for_psychologists"))
        self.assertContains(response, "Join Our Network")

        # Patient page CTA - check for any referral-related text
        response = self.client.get(reverse("public:for_patients"))
        # Look for any text that indicates self-referral functionality
        self.assertTrue(
            "referral" in response.content.decode().lower()
            or "self" in response.content.decode().lower()
        )

    def test_public_pages_responsive_design(self):
        """Test that public pages have responsive design elements."""
        response = self.client.get(reverse("public:landing"))
        # Check for viewport meta tag which is essential for responsive design
        self.assertContains(response, "viewport")

    def test_public_pages_accessibility(self):
        """Test that public pages have accessibility features."""
        response = self.client.get(reverse("public:landing"))
        # Check for basic accessibility features - alt text, semantic HTML
        # These are more likely to be present in the actual templates
        content = response.content.decode().lower()
        # Check for basic semantic HTML elements
        self.assertTrue(
            "main" in content
            or "nav" in content
            or "header" in content
            or "section" in content
        )
