"""
Management command to test the notification system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from inbox.models import Notification, NotificationPreference
from inbox.services import NotificationService
from referrals.models import Referral
from accounts.models import User

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the notification system by creating sample notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to send notifications to (default: first user)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of test notifications to create (default: 5)',
        )
        parser.add_argument(
            '--notification-type',
            type=str,
            choices=[choice[0] for choice in Notification.NotificationType.choices],
            help='Specific notification type to test',
        )

    def handle(self, *args, **options):
        """Create test notifications."""
        
        # Get user
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found')
                )
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No users found. Please create a user first.')
                )
                return
        
        self.stdout.write(f'Creating test notifications for user: {user.get_full_name()}')
        
        # Create notification preferences if they don't exist
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        if created:
            self.stdout.write('Created notification preferences for user')
        
        # Get or create a test referral
        referral = self.get_or_create_test_referral(user)
        
        # Create test notifications
        service = NotificationService()
        count = options['count']
        notification_type = options['notification_type']
        
        notification_types = [
            Notification.NotificationType.REFERRAL_UPDATE,
            Notification.NotificationType.MATCHING_COMPLETE,
            Notification.NotificationType.INVITATION,
            Notification.NotificationType.RESPONSE,
            Notification.NotificationType.APPOINTMENT,
            Notification.NotificationType.SYSTEM,
            Notification.NotificationType.REMINDER,
        ]
        
        if notification_type:
            notification_types = [notification_type]
        
        created_notifications = []
        
        for i in range(count):
            # Cycle through notification types
            current_type = notification_types[i % len(notification_types)]
            
            # Create notification data
            notification_data = self.get_notification_data(current_type, i + 1, referral)
            
            # Create notification
            notification = service.create_notification(
                user=user,
                notification_type=current_type,
                title=notification_data['title'],
                message=notification_data['message'],
                priority=notification_data['priority'],
                is_important=notification_data['is_important'],
                referral=referral if current_type in ['referral_update', 'matching_complete'] else None,
            )
            
            created_notifications.append(notification)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {current_type} notification: {notification.title}'
                )
            )
        
        # Test notification stats
        stats = service.get_notification_stats(user)
        self.stdout.write(f'\nNotification stats for {user.get_full_name()}:')
        self.stdout.write(f'  Total: {stats["total"]}')
        self.stdout.write(f'  Unread: {stats["unread"]}')
        self.stdout.write(f'  Important: {stats["important"]}')
        
        # Test marking notifications as read
        if created_notifications:
            first_notification = created_notifications[0]
            if service.mark_as_read(str(first_notification.id), user):
                self.stdout.write(
                    self.style.SUCCESS(f'Marked notification as read: {first_notification.title}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to mark notification as read')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {len(created_notifications)} test notifications')
        )

    def get_or_create_test_referral(self, user):
        """Get or create a test referral."""
        try:
            return Referral.objects.first()
        except Referral.DoesNotExist:
            # Create test users for patient and GP if they don't exist
            patient_user, _ = User.objects.get_or_create(
                email='test.patient@example.com',
                defaults={
                    'user_type': User.UserType.PATIENT,
                    'first_name': 'Test',
                    'last_name': 'Patient',
                    'date_of_birth': timezone.now().date().replace(year=1990),
                }
            )
            
            gp_user, _ = User.objects.get_or_create(
                email='test.gp@example.com',
                defaults={
                    'user_type': User.UserType.GP,
                    'first_name': 'Test',
                    'last_name': 'GP',
                }
            )
            
            # Create test referral
            referral = Referral.objects.create(
                patient=patient_user,
                referrer=gp_user,
                condition_description='Test condition for notification testing',
                urgency='routine',
                language_requirements='English',
            )
            
            self.stdout.write('Created test referral for notification testing')
            return referral

    def get_notification_data(self, notification_type, index, referral):
        """Get notification data based on type."""
        
        base_data = {
            'priority': 'medium',
            'is_important': False,
        }
        
        if notification_type == Notification.NotificationType.REFERRAL_UPDATE:
            return {
                **base_data,
                'title': f'Referral Update #{index}',
                'message': f'This is a test referral update notification #{index}. The referral has been updated with new information.',
            }
        
        elif notification_type == Notification.NotificationType.MATCHING_COMPLETE:
            return {
                **base_data,
                'title': f'Matching Complete #{index}',
                'message': f'This is a test matching complete notification #{index}. We found {index * 2} potential matches for the referral.',
            }
        
        elif notification_type == Notification.NotificationType.INVITATION:
            return {
                **base_data,
                'title': f'New Invitation #{index}',
                'message': f'This is a test invitation notification #{index}. You have been invited to provide psychological services.',
            }
        
        elif notification_type == Notification.NotificationType.RESPONSE:
            return {
                **base_data,
                'title': f'Response Received #{index}',
                'message': f'This is a test response notification #{index}. A response has been received for your invitation.',
            }
        
        elif notification_type == Notification.NotificationType.APPOINTMENT:
            return {
                **base_data,
                'title': f'Appointment Scheduled #{index}',
                'message': f'This is a test appointment notification #{index}. An appointment has been scheduled for tomorrow.',
            }
        
        elif notification_type == Notification.NotificationType.SYSTEM:
            return {
                **base_data,
                'title': f'System Notification #{index}',
                'message': f'This is a test system notification #{index}. Important system information that requires your attention.',
                'is_important': index % 3 == 0,  # Make every 3rd system notification important
            }
        
        elif notification_type == Notification.NotificationType.REMINDER:
            return {
                **base_data,
                'title': f'Reminder #{index}',
                'message': f'This is a test reminder notification #{index}. A friendly reminder about an upcoming task.',
                'priority': 'low',
            }
        
        # Default fallback
        return {
            **base_data,
            'title': f'Test Notification #{index}',
            'message': f'This is a test notification #{index} of type {notification_type}.',
        }
