"""
Notification services for ReferWell Direct.
"""
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from celery import shared_task

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.template import Context, Template
from django.utils import timezone

from .models import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationTemplate,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications and delivery.
    """

    def __init__(self) -> None:
        self.cache_timeout = getattr(settings, "NOTIFICATION_CACHE_TIMEOUT", 300)

    def create_notification(
        self,
        user: "AbstractBaseUser",
        notification_type: str,
        title: str,
        message: str,
        priority: str = "medium",
        is_important: bool = False,
        referral: Any = None,
        candidate: Any = None,
        appointment: Any = None,
        **kwargs: Any,
    ) -> Notification:
        """
        Create a new notification for a user.
        """
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                is_important=is_important,
                referral=referral,
                candidate=candidate,
                appointment=appointment,
            )

            # Send notification via appropriate channels
            self._send_notification(notification)

            logger.info(f"Created notification {notification.id} for user {user.id}")  # type: ignore[attr-defined]
            return notification

        except Exception as e:
            logger.error(f"Failed to create notification for user {user.id}: {str(e)}")  # type: ignore[attr-defined]
            raise

    def create_notification_from_template(
        self,
        user: "AbstractBaseUser",
        template_name: str,
        context: dict[str, Any],
        notification_type: str | None = None,
        **kwargs: Any,
    ) -> Notification | None:
        """
        Create a notification from a template.
        """
        try:
            template = NotificationTemplate.objects.get(
                name=template_name, is_active=True
            )

            # Render templates
            title_template = Template(template.title_template)
            message_template = Template(template.message_template)

            template_context = Context(context)
            title = title_template.render(template_context)
            message = message_template.render(template_context)

            return self.create_notification(
                user=user,
                notification_type=notification_type or template.notification_type,
                title=title,
                message=message,
                **kwargs,
            )

        except NotificationTemplate.DoesNotExist:
            logger.warning(f"Template {template_name} not found")
            return None
        except Exception as e:
            logger.error(
                f"Failed to create notification from template {template_name}: {str(e)}"
            )
            return None

    def _send_notification(self, notification: Notification) -> None:
        """
        Send notification via appropriate channels based on user preferences.
        """
        try:
            # Get user preferences
            preferences = self._get_user_preferences(notification.user)

            # Check quiet hours
            if preferences and preferences.is_quiet_hours():
                logger.info(
                    f"Notification {notification.id} suppressed due to quiet hours"
                )
                return

            # Get delivery method for this notification type
            delivery_method = (
                preferences.get_delivery_method(notification.notification_type)
                if preferences
                else "in_app"
            )

            # Send via appropriate channels
            if delivery_method in ["in_app", "all"]:
                self._send_in_app_notification(notification)

            if (
                delivery_method in ["email", "all"]
                and preferences
                and preferences.email_notifications_enabled
            ):
                self._send_email_notification(notification, preferences)

            if (
                delivery_method in ["push", "all"]
                and preferences
                and preferences.push_notifications_enabled
            ):
                self._send_push_notification(notification)

        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")

    def _get_user_preferences(
        self, user: "AbstractBaseUser"
    ) -> NotificationPreference | None:
        """
        Get user notification preferences with caching.
        """
        cache_key = f"notification_preferences_{user.id}"  # type: ignore[attr-defined]
        preferences = cache.get(cache_key)

        if preferences is None:
            preferences, created = NotificationPreference.objects.get_or_create(
                user=user
            )
            cache.set(cache_key, preferences, self.cache_timeout)

        return preferences

    def _send_in_app_notification(self, notification: Notification) -> None:
        """
        Send in-app notification via WebSocket.
        """
        try:
            # Get active channels for user
            channels = NotificationChannel.objects.filter(
                user=notification.user, is_active=True
            )

            for channel in channels:
                self._send_websocket_message(
                    channel.channel_name,
                    {
                        "type": "notification",
                        "notification": {
                            "id": str(notification.id),
                            "title": notification.title,
                            "message": notification.message,
                            "notification_type": notification.notification_type,
                            "priority": notification.priority,
                            "is_important": notification.is_important,
                            "created_at": notification.created_at.isoformat(),
                        },
                    },
                )

        except Exception as e:
            logger.error(
                f"Failed to send in-app notification {notification.id}: {str(e)}"
            )

    def _send_email_notification(
        self, notification: Notification, preferences: NotificationPreference
    ) -> None:
        """
        Send email notification.
        """
        try:
            # Get email template
            template = NotificationTemplate.objects.filter(
                notification_type=notification.notification_type, is_active=True
            ).first()

            if not template or not template.email_subject_template:
                logger.warning(
                    f"No email template found for {notification.notification_type}"
                )
                return

            # Render email templates
            subject_template = Template(template.email_subject_template)
            body_template = Template(
                template.email_body_template or template.message_template
            )

            context = Context(
                {
                    "user": notification.user,
                    "notification": notification,
                    "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
                }
            )

            subject = subject_template.render(context)
            body = body_template.render(context)

            # Send email (stubbed for now)
            if getattr(settings, "FEATURE_EMAIL_NOTIFICATIONS", False):
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(
                        settings, "DEFAULT_FROM_EMAIL", "noreply@referwell.com"
                    ),
                    recipient_list=[notification.user.email],
                    fail_silently=False,
                )
            else:
                logger.info(f"Email notification stubbed: {subject}")

        except Exception as e:
            logger.error(
                f"Failed to send email notification {notification.id}: {str(e)}"
            )

    def _send_push_notification(self, notification: Notification) -> None:
        """
        Send push notification (stubbed for now).
        """
        try:
            if getattr(settings, "FEATURE_PUSH_NOTIFICATIONS", False):
                # TODO: Implement actual push notification service
                logger.info(f"Push notification stubbed: {notification.title}")
            else:
                logger.info(f"Push notifications disabled: {notification.title}")

        except Exception as e:
            logger.error(
                f"Failed to send push notification {notification.id}: {str(e)}"
            )

    def _send_websocket_message(
        self, channel_name: str, message: dict[str, Any]
    ) -> None:
        """
        Send message via WebSocket (stubbed for now).
        """
        try:
            if getattr(settings, "FEATURE_WEBSOCKET_NOTIFICATIONS", False):
                # TODO: Implement actual WebSocket message sending
                logger.info(f"WebSocket message stubbed to {channel_name}: {message}")
            else:
                logger.info(f"WebSocket notifications disabled: {message}")

        except Exception as e:
            logger.error(
                f"Failed to send WebSocket message to {channel_name}: {str(e)}"
            )

    def mark_as_read(self, notification_id: str, user: "AbstractBaseUser") -> bool:
        """
        Mark a notification as read.
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()

            # Send read status via WebSocket
            self._send_read_status(notification)

            return True

        except Notification.DoesNotExist:
            logger.warning(
                f"Notification {notification_id} not found for user {user.id}"  # type: ignore[attr-defined]
            )
            return False
        except Exception as e:
            logger.error(
                f"Failed to mark notification {notification_id} as read: {str(e)}"
            )
            return False

    def _send_read_status(self, notification: Notification) -> None:
        """
        Send read status via WebSocket.
        """
        try:
            channels = NotificationChannel.objects.filter(
                user=notification.user, is_active=True
            )

            for channel in channels:
                self._send_websocket_message(
                    channel.channel_name,
                    {
                        "type": "notification_read",
                        "notification_id": str(notification.id),
                        "read_at": notification.read_at.isoformat()
                        if notification.read_at
                        else None,
                    },
                )

        except Exception as e:
            logger.error(
                f"Failed to send read status for notification {notification.id}: {str(e)}"
            )

    def get_user_notifications(
        self,
        user: "AbstractBaseUser",
        unread_only: bool = False,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """
        Get notifications for a user with optional filtering.
        """
        try:
            queryset = Notification.objects.filter(user=user)

            if unread_only:
                queryset = queryset.filter(is_read=False)

            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)

            return list(queryset.order_by("-created_at")[offset : offset + limit])

        except Exception as e:
            logger.error(f"Failed to get notifications for user {user.id}: {str(e)}")  # type: ignore[attr-defined]
            return []

    def get_notification_stats(self, user: "AbstractBaseUser") -> dict[str, int]:
        """
        Get notification statistics for a user.
        """
        try:
            stats = {
                "total": Notification.objects.filter(user=user).count(),
                "unread": Notification.objects.filter(user=user, is_read=False).count(),
                "important": Notification.objects.filter(
                    user=user, is_important=True, is_read=False
                ).count(),
            }

            # Add counts by type
            for notification_type, _ in Notification.NotificationType.choices:
                stats[f"{notification_type}_unread"] = Notification.objects.filter(
                    user=user, notification_type=notification_type, is_read=False
                ).count()

            return stats

        except Exception as e:
            logger.error(
                f"Failed to get notification stats for user {user.id}: {str(e)}"  # type: ignore[attr-defined]
            )
            return {}


class NotificationChannelService:
    """
    Service for managing WebSocket notification channels.
    """

    def create_channel(
        self, user: "AbstractBaseUser", channel_name: str | None = None
    ) -> NotificationChannel:
        """
        Create a new notification channel for a user.
        """
        if not channel_name:
            channel_name = f"user_{user.id}_{timezone.now().timestamp()}"  # type: ignore[attr-defined]

        channel = NotificationChannel.objects.create(
            user=user, channel_name=channel_name
        )

        logger.info(f"Created notification channel {channel_name} for user {user.id}")  # type: ignore[attr-defined]
        return channel

    def deactivate_channel(self, channel_name: str) -> bool:
        """
        Deactivate a notification channel.
        """
        try:
            channel = NotificationChannel.objects.get(channel_name=channel_name)
            channel.is_active = False
            channel.save(update_fields=["is_active"])

            logger.info(f"Deactivated notification channel {channel_name}")
            return True

        except NotificationChannel.DoesNotExist:
            logger.warning(f"Notification channel {channel_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate channel {channel_name}: {str(e)}")
            return False


# Celery tasks for background notification processing
@shared_task  # type: ignore[misc]
def send_notification_async(notification_id: str) -> None:
    """
    Async task to send a notification.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        service = NotificationService()
        service._send_notification(notification)

    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found for async sending")
    except Exception as e:
        logger.error(f"Failed to send notification {notification_id} async: {str(e)}")


@shared_task  # type: ignore[misc]
def cleanup_old_notifications() -> None:
    """
    Clean up old notifications (older than 30 days).
    """
    try:
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=30)

        old_notifications = Notification.objects.filter(
            created_at__lt=cutoff_date, is_read=True
        )

        count = old_notifications.count()
        old_notifications.delete()

        logger.info(f"Cleaned up {count} old notifications")

    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {str(e)}")


@shared_task  # type: ignore[misc]
def send_digest_notifications() -> None:
    """
    Send daily digest notifications to users.
    """
    try:
        # Get users who have unread notifications
        users_with_notifications = User.objects.filter(
            notifications__is_read=False
        ).distinct()

        for user in users_with_notifications:
            unread_count = Notification.objects.filter(user=user, is_read=False).count()

            if unread_count > 0:
                service = NotificationService()
                service.create_notification(
                    user=user,
                    notification_type="system",
                    title="Daily Digest",
                    message=f"You have {unread_count} unread notifications.",
                    priority="low",
                )

        logger.info(
            f"Sent digest notifications to {users_with_notifications.count()} users"
        )

    except Exception as e:
        logger.error(f"Failed to send digest notifications: {str(e)}")
