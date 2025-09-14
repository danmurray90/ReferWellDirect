"""
Tests for accounts app.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, Organisation, UserOrganisation
import json

User = get_user_model()


class UserModelTest(TestCase):
    """
    Test cases for User model.
    """
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'user_type': User.UserType.GP,
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.user_type, User.UserType.GP)
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_verified)
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.first_name} {user.last_name} ({user.get_user_type_display()})"
        self.assertEqual(str(user), expected)
    
    def test_user_full_name(self):
        """Test user full name property."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'John Doe')
    
    def test_user_type_properties(self):
        """Test user type properties."""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.is_gp)
        self.assertFalse(user.is_patient)
        self.assertFalse(user.is_psychologist)
        self.assertFalse(user.is_admin)
    
    def test_user_validation(self):
        """Test user validation."""
        # Test required fields
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')
        
        # Test unique email
        User.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create_user(**self.user_data)


class OrganisationModelTest(TestCase):
    """
    Test cases for Organisation model.
    """
    
    def setUp(self):
        self.organisation_data = {
            'name': 'Test GP Practice',
            'organisation_type': Organisation.OrganisationType.GP_PRACTICE,
            'email': 'test@gppractice.com',
            'phone': '+44123456789',
            'address_line_1': '123 Test Street',
            'city': 'London',
            'postcode': 'SW1A 1AA',
            'country': 'United Kingdom'
        }
    
    def test_create_organisation(self):
        """Test creating an organisation."""
        org = Organisation.objects.create(**self.organisation_data)
        self.assertEqual(org.name, 'Test GP Practice')
        self.assertEqual(org.organisation_type, Organisation.OrganisationType.GP_PRACTICE)
        self.assertEqual(org.email, 'test@gppractice.com')
        self.assertTrue(org.is_active)
        self.assertFalse(org.is_verified)
    
    def test_organisation_str_representation(self):
        """Test organisation string representation."""
        org = Organisation.objects.create(**self.organisation_data)
        self.assertEqual(str(org), 'Test GP Practice')


class UserOrganisationModelTest(TestCase):
    """
    Test cases for UserOrganisation model.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            user_type=User.UserType.GP,
            password='testpass123'
        )
        self.organisation = Organisation.objects.create(
            name='Test GP Practice',
            organisation_type=Organisation.OrganisationType.GP_PRACTICE,
            email='test@gppractice.com',
            address_line_1='123 Test Street',
            city='London',
            postcode='SW1A 1AA'
        )
    
    def test_create_user_organisation(self):
        """Test creating a user-organisation relationship."""
        user_org = UserOrganisation.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=UserOrganisation.Role.MEMBER
        )
        self.assertEqual(user_org.user, self.user)
        self.assertEqual(user_org.organisation, self.organisation)
        self.assertEqual(user_org.role, UserOrganisation.Role.MEMBER)
        self.assertTrue(user_org.is_active)
    
    def test_user_organisation_str_representation(self):
        """Test user-organisation string representation."""
        user_org = UserOrganisation.objects.create(
            user=self.user,
            organisation=self.organisation,
            role=UserOrganisation.Role.MEMBER
        )
        expected = f"{self.user.get_full_name()} - {self.organisation.name} (Member)"
        self.assertEqual(str(user_org), expected)


class UserViewsTest(TestCase):
    """
    Test cases for user views.
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            user_type=User.UserType.GP,
            password='testpass123'
        )
    
    def test_signin_view_get(self):
        """Test sign-in view GET request."""
        response = self.client.get(reverse('accounts:signin'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')
    
    def test_signin_view_post_success(self):
        """Test sign-in view POST request with valid credentials."""
        response = self.client.post(reverse('accounts:signin'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('referrals:dashboard'))
    
    def test_signin_view_post_invalid(self):
        """Test sign-in view POST request with invalid credentials."""
        response = self.client.post(reverse('accounts:signin'), {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
    
    def test_profile_view_unauthenticated(self):
        """Test profile view for unauthenticated user."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(response, f"{reverse('accounts:signin')}?next={reverse('accounts:profile')}")


class UserAPITest(APITestCase):
    """
    Test cases for user API views.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            user_type=User.UserType.GP,
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            user_type=User.UserType.ADMIN,
            password='adminpass123',
            is_staff=True
        )
    
    def test_user_list_api_authenticated(self):
        """Test user list API for authenticated user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('accounts_api:user-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # Both users
    
    def test_user_list_api_unauthenticated(self):
        """Test user list API for unauthenticated user."""
        response = self.client.get(reverse('accounts_api:user-list'))
        self.assertEqual(response.status_code, 401)
    
    def test_user_detail_api(self):
        """Test user detail API."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('accounts_api:user-detail', kwargs={'pk': self.user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_user_create_api(self):
        """Test user create API."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': User.UserType.PATIENT,
            'password': 'newpass123'
        }
        response = self.client.post(reverse('accounts_api:user-list'), data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 3)
    
    def test_user_update_api(self):
        """Test user update API."""
        self.client.force_authenticate(user=self.user)
        data = {'first_name': 'Updated'}
        response = self.client.patch(reverse('accounts_api:user-detail', kwargs={'pk': self.user.id}), data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
