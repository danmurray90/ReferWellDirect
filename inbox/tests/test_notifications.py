"""
Tests for the notification system.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from freezegun import freeze_time
from .models import Notification, NotificationTemplate, NotificationPreference, NotificationChannel
from .services import NotificationService, NotificationChannelService
from referrals.models import Referral
from accounts.models import Patient, GP

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test notification models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth=timezone.now().date().replace(year=1990),
            nhs_number='1234567890'
        )
        
        self.gp = GP.objects.create(
            user=self.user,
            gmc_number='12345678',
            specialty='General Practice'
        )
        
        self.referral = Referral.objects.create(
            patient=self.patient,
            referrer=self.gp,
            condition_description='Test condition',
            urgency='routine',
            language_requirements='English'
        )
    
    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='referral_update',
            title='Test Notification',
            message='This is a test notification',
            priority='medium',
            referral=self.referral
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'referral_update')
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertEqual(notification.priority, 'medium')
        self.assertEqual(notification.referral, self.referral)
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_important)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNone(notification.read_at)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='referral_update',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_template_creation(self):
        """Test creating notification templates."""
        template = NotificationTemplate.objects.create(
            name='test_template',
            notification_type='referral_update',
            title_template='Test: {{ referral.patient.get_full_name }}',
            message_template='Test message for {{ referral.patient.get_full_name }}',
            email_subject_template='Test Email: {{ referral.patient.get_full_name }}',
            email_body_template='Test email body for {{ referral.patient.get_full_name }}'
        )
        
        self.assertEqual(template.name, 'test_template')
        self.assertEqual(template.notification_type, 'referral_update')
        self.assertTrue(template.is_active)
    
    def test_notification_preference_creation(self):
        """Test creating notification preferences."""
        preferences = NotificationPreference.objects.create(
            user=self.user,
            referral_update_method='email',
            matching_complete_method='in_app',
            email_notifications_enabled=True,
            push_notifications_enabled=False
        )
        
        self.assertEqual(preferences.user, self.user)
        self.assertEqual(preferences.referral_update_method, 'email')
        self.assertEqual(preferences.matching_complete_method, 'in_app')
        self.assertTrue(preferences.email_notifications_enabled)
        self.assertFalse(preferences.push_notifications_enabled)
    
    def test_notification_preference_get_delivery_method(self):
        """Test getting delivery method for notification type."""
        preferences = NotificationPreference.objects.create(
            user=self.user,
            referral_update_method='email',
            matching_complete_method='in_app'
        )
        
        self.assertEqual(
            preferences.get_delivery_method('referral_update'),
            'email'
        )
        self.assertEqual(
            preferences.get_delivery_method('matching_complete'),
            'in_app'
        )
    
    def test_notification_preference_quiet_hours(self):
        """Test quiet hours functionality."""
        preferences = NotificationPreference.objects.create(
            user=self.user,
            quiet_hours_start=timezone.now().time().replace(hour=22),
            quiet_hours_end=timezone.now().time().replace(hour=8)
        )
        
        # Test during quiet hours
        with freeze_time('2023-01-01 23:00:00'):
            self.assertTrue(preferences.is_quiet_hours())
        
        # Test outside quiet hours
        with freeze_time('2023-01-01 12:00:00'):
            self.assertFalse(preferences.is_quiet_hours())
    
    def test_notification_channel_creation(self):
        """Test creating notification channels."""
        channel = NotificationChannel.objects.create(
            user=self.user,
            channel_name='test_channel_123'
        )
        
        self.assertEqual(channel.user, self.user)
        self.assertEqual(channel.channel_name, 'test_channel_123')
        self.assertTrue(channel.is_active)


class NotificationServiceTests(TestCase):
    """Test notification service."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.service = NotificationService()
    
    def test_create_notification(self):
        """Test creating a notification via service."""
        notification = self.service.create_notification(
            user=self.user,
            notification_type='referral_update',
            title='Test Notification',
            message='This is a test notification',
            priority='medium'
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
    
    @patch('inbox.services.NotificationService._send_notification')
    def test_create_notification_sends_notification(self, mock_send):
        """Test that creating notification triggers sending."""
        self.service.create_notification(
            user=self.user,
            notification_type='referral_update',
            title='Test Notification',
            message='This is a test notification'
        )
        
        mock_send.assert_called_once()
    
    def test_create_notification_from_template(self):
        """Test creating notification from template."""
        template = NotificationTemplate.objects.create(
            name='test_template',
            notification_type='referral_update',
            title_template='Hello {{ user.first_name }}',
            message_template='Welcome {{ user.first_name }} {{ user.last_name }}'
        )
        
        notification = self.service.create_notification_from_template(
            user=self.user,
            template_name='test_template',
            context={'user': self.user}
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.title, 'Hello Test')
        self.assertEqual(notification.message, 'Welcome Test User')
    
    def test_get_user_notifications(self):
        """Test getting user notifications."""
        # Create test notifications
        Notification.objects.create(
            user=self.user,
            notification_type='referral_update',
            title='Notification 1',
            message='Message 1'
        )
        
        Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Notification 2',
            message='Message 2',
            is_read=True
        )
        
        # Test getting all notifications
        notifications = self.service.get_user_notifications(self.user)
        self.assertEqual(len(notifications), 2)
        
        # Test getting unread only
        unread_notifications = self.service.get_user_notifications(
            self.user, unread_only=True
        )
        self.assertEqual(len(unread_notifications), 1)
        
        # Test filtering by type
        referral_notifications = self.service.get_user_notifications(
            self.user, notification_type='referral_update'
        )
        self.assertEqual(len(referral_notifications), 1)
    
    def test_get_notification_stats(self):
        """Test getting notification statistics."""
        # Create test notifications
        Notification.objects.create(
            user=self.user,
            notification_type='referral_update',
            title='Notification 1',
            message='Message 1'
        )
        
        Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Notification 2',
            message='Message 2',
            is_read=True,
            is_important=True
        )
        
        stats = self.service.get_notification_stats(self.user)
        
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['unread'], 1)
        self.assertEqual(stats['important'], 1)
        self.assertEqual(stats['referral_update_unread'], 1)
        self.assertEqual(stats['system_unread'], 0)
    
    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='referral_update',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertFalse(notification.is_read)
        
        success = self.service.mark_as_read(str(notification.id), self.user)
        
        self.assertTrue(success)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_as_read_nonexistent(self):
        """Test marking non-existent notification as read."""
        success = self.service.mark_as_read('00000000-0000-0000-0000-000000000000', self.user)
        self.assertFalse(success)
    
    def test_mark_as_read_wrong_user(self):
        """Test marking notification as read for wrong user."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        notification = Notification.objects.create(
            user=other_user,
            notification_type='referral_update',
            title='Test Notification',
            message='This is a test notification'
        )
        
        success = self.service.mark_as_read(str(notification.id), self.user)
        self.assertFalse(success)


class NotificationChannelServiceTests(TestCase):
    """Test notification channel service."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.service = NotificationChannelService()
    
    def test_create_channel(self):
        """Test creating a notification channel."""
        channel = self.service.create_channel(self.user, 'test_channel')
        
        self.assertEqual(channel.user, self.user)
        self.assertEqual(channel.channel_name, 'test_channel')
        self.assertTrue(channel.is_active)
    
    def test_create_channel_without_name(self):
        """Test creating channel without specifying name."""
        channel = self.service.create_channel(self.user)
        
        self.assertEqual(channel.user, self.user)
        self.assertTrue(channel.channel_name.startswith('user_'))
        self.assertTrue(channel.is_active)
    
    def test_deactivate_channel(self):
        """Test deactivating a channel."""
        channel = NotificationChannel.objects.create(
            user=self.user,
            channel_name='test_channel'
        )
        
        success = self.service.deactivate_channel('test_channel')
        
        self.assertTrue(success)
        channel.refresh_from_db()
        self.assertFalse(channel.is_active)
    
    def test_deactivate_nonexistent_channel(self):
        """Test deactivating non-existent channel."""
        success = self.service.deactivate_channel('nonexistent_channel')
        self.assertFalse(success)


class NotificationAPITests(APITestCase):
    """Test notification API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Create test notifications
        self.notification1 = Notification.objects.create(
            user=self.user,
            notification_type='referral_update',
            title='Test Notification 1',
            message='This is test notification 1'
        )
        
        self.notification2 = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Test Notification 2',
            message='This is test notification 2',
            is_read=True
        )
    
    def test_list_notifications(self):
        """Test listing notifications."""
        url = reverse('inbox_api:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_notifications_filtered(self):
        """Test listing notifications with filters."""
        url = reverse('inbox_api:notification-list')
        response = self.client.get(url, {'is_read': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.notification1.id))
    
    def test_get_notification_detail(self):
        """Test getting notification detail."""
        url = reverse('inbox_api:notification-detail', args=[self.notification1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Notification 1')
    
    def test_mark_notification_read(self):
        """Test marking notification as read."""
        url = reverse('inbox_api:notification-mark-as-read', args=[self.notification1.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
    
    def test_bulk_mark_read(self):
        """Test bulk marking notifications as read."""
        url = reverse('inbox_api:notification-mark-read')
        data = {
            'notification_ids': [str(self.notification1.id)]
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)
    
    def test_bulk_action(self):
        """Test bulk actions on notifications."""
        url = reverse('inbox_api:notification-bulk-action')
        data = {
            'action': 'mark_read',
            'notification_ids': [str(self.notification1.id)]
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)
    
    def test_get_notification_stats(self):
        """Test getting notification statistics."""
        url = reverse('inbox_api:notification-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['unread'], 1)
    
    def test_create_notification(self):
        """Test creating a notification."""
        url = reverse('inbox_api:notification-list')
        data = {
            'notification_type': 'system',
            'title': 'New Test Notification',
            'message': 'This is a new test notification',
            'priority': 'high'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Notification')
    
    def test_notification_preferences(self):
        """Test notification preferences API."""
        url = reverse('inbox_api:notification-preference-list')
        
        # Test getting preferences (should create if not exist)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test updating preferences
        data = {
            'referral_update_method': 'email',
            'matching_complete_method': 'in_app',
            'email_notifications_enabled': True
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['referral_update_method'], 'email')


class NotificationTemplateAPITests(APITestCase):
    """Test notification template API."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.template = NotificationTemplate.objects.create(
            name='test_template',
            notification_type='referral_update',
            title_template='Test: {{ user.first_name }}',
            message_template='Hello {{ user.first_name }}'
        )
    
    def test_list_templates(self):
        """Test listing notification templates."""
        url = reverse('inbox_api:notification-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_get_template_detail(self):
        """Test getting template detail."""
        url = reverse('inbox_api:notification-template-detail', args=[self.template.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test_template')
    
    def test_create_template(self):
        """Test creating a template."""
        url = reverse('inbox_api:notification-template-list')
        data = {
            'name': 'new_template',
            'notification_type': 'system',
            'title_template': 'New: {{ user.first_name }}',
            'message_template': 'New message for {{ user.first_name }}'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_template')
    
    def test_update_template(self):
        """Test updating a template."""
        url = reverse('inbox_api:notification-template-detail', args=[self.template.id])
        data = {
            'title_template': 'Updated: {{ user.first_name }}'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title_template'], 'Updated: {{ user.first_name }}')


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
)
class NotificationCacheTests(TestCase):
    """Test notification caching functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.service = NotificationService()
    
    def tearDown(self):
        cache.clear()
    
    def test_user_preferences_caching(self):
        """Test that user preferences are cached."""
        # Create preferences
        preferences = NotificationPreference.objects.create(
            user=self.user,
            referral_update_method='email'
        )
        
        # First call should hit database
        with self.assertNumQueries(1):
            cached_preferences = self.service._get_user_preferences(self.user)
        
        # Second call should hit cache
        with self.assertNumQueries(0):
            cached_preferences = self.service._get_user_preferences(self.user)
        
        self.assertEqual(cached_preferences.referral_update_method, 'email')
