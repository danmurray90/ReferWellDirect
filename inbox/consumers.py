"""
WebSocket consumers for real-time notifications.
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth import get_user_model

from .models import NotificationChannel

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.channel_name = f"user_{self.user.id}_{self.channel_name}"

        if not self.user.is_authenticated:
            await self.close()
            return

        # Join user's notification group
        await self.channel_layer.group_add(
            f"notifications_{self.user.id}", self.channel_name
        )

        # Create or update notification channel
        await self.create_notification_channel()

        await self.accept()

        logger.info(f"WebSocket connected for user {self.user.id}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "user") and self.user.is_authenticated:
            # Leave user's notification group
            await self.channel_layer.group_discard(
                f"notifications_{self.user.id}", self.channel_name
            )

            # Deactivate notification channel
            await self.deactivate_notification_channel()

            logger.info(f"WebSocket disconnected for user {self.user.id}")

    async def receive(self, text_data):
        """Handle WebSocket message."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                await self.send(
                    text_data=json.dumps(
                        {"type": "pong", "timestamp": data.get("timestamp")}
                    )
                )

            elif message_type == "mark_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "mark_read_response",
                                "notification_id": notification_id,
                                "success": success,
                            }
                        )
                    )

            elif message_type == "get_stats":
                stats = await self.get_notification_stats()
                await self.send(
                    text_data=json.dumps({"type": "stats_response", "stats": stats})
                )

        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    async def notification_message(self, event):
        """Handle notification message from group."""
        await self.send(
            text_data=json.dumps(
                {"type": "notification", "notification": event["notification"]}
            )
        )

    async def notification_read(self, event):
        """Handle notification read status update."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification_read",
                    "notification_id": event["notification_id"],
                    "read_at": event["read_at"],
                }
            )
        )

    @database_sync_to_async
    def create_notification_channel(self):
        """Create or update notification channel in database."""
        try:
            channel, created = NotificationChannel.objects.get_or_create(
                channel_name=self.channel_name,
                defaults={"user": self.user, "is_active": True},
            )

            if not created:
                channel.is_active = True
                channel.save(update_fields=["is_active"])

            logger.info(
                f"Notification channel {'created' if created else 'updated'}: {self.channel_name}"
            )

        except Exception as e:
            logger.error(f"Failed to create notification channel: {str(e)}")

    @database_sync_to_async
    def deactivate_notification_channel(self):
        """Deactivate notification channel in database."""
        try:
            NotificationChannel.objects.filter(channel_name=self.channel_name).update(
                is_active=False
            )

            logger.info(f"Notification channel deactivated: {self.channel_name}")

        except Exception as e:
            logger.error(f"Failed to deactivate notification channel: {str(e)}")

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read."""
        try:
            from .services import NotificationService

            service = NotificationService()
            return service.mark_as_read(notification_id, self.user)
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False

    @database_sync_to_async
    def get_notification_stats(self):
        """Get notification statistics for user."""
        try:
            from .services import NotificationService

            service = NotificationService()
            return service.get_notification_stats(self.user)
        except Exception as e:
            logger.error(f"Failed to get notification stats: {str(e)}")
            return {}


class NotificationGroupConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for group notifications (admin, system-wide).
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.group_name = self.scope["url_route"]["kwargs"]["group_name"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Check if user has permission to join this group
        if not await self.has_group_permission():
            await self.close()
            return

        # Join group
        await self.channel_layer.group_add(
            f"group_{self.group_name}", self.channel_name
        )

        await self.accept()

        logger.info(
            f"WebSocket connected to group {self.group_name} for user {self.user.id}"
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "user") and self.user.is_authenticated:
            # Leave group
            await self.channel_layer.group_discard(
                f"group_{self.group_name}", self.channel_name
            )

            logger.info(
                f"WebSocket disconnected from group {self.group_name} for user {self.user.id}"
            )

    async def receive(self, text_data):
        """Handle WebSocket message."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                await self.send(
                    text_data=json.dumps(
                        {"type": "pong", "timestamp": data.get("timestamp")}
                    )
                )

        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    async def group_message(self, event):
        """Handle group message."""
        await self.send(
            text_data=json.dumps({"type": "group_message", "message": event["message"]})
        )

    @database_sync_to_async
    def has_group_permission(self):
        """Check if user has permission to join this group."""
        # Implement group permission logic here
        # For now, allow all authenticated users
        return self.user.is_authenticated
