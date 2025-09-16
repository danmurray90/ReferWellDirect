"""
Serializers for ReferWell Direct inbox app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, NotificationTemplate, NotificationPreference, NotificationChannel

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    referral_id = serializers.UUIDField(source='referral.id', read_only=True)
    candidate_id = serializers.UUIDField(source='candidate.id', read_only=True)
    appointment_id = serializers.UUIDField(source='appointment.id', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name', 'user_email', 'notification_type', 'title', 'message',
            'priority', 'is_read', 'is_important', 'referral', 'referral_id', 'candidate',
            'candidate_id', 'appointment', 'appointment_id', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def validate_notification_type(self, value):
        """Validate notification type."""
        valid_types = [choice[0] for choice in Notification.NotificationType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid notification type. Must be one of: {valid_types}")
        return value
    
    def validate_priority(self, value):
        """Validate priority."""
        valid_priorities = [choice[0] for choice in Notification.Priority.choices]
        if value not in valid_priorities:
            raise serializers.ValidationError(f"Invalid priority. Must be one of: {valid_priorities}")
        return value


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for notification lists.
    """
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'priority',
            'is_read', 'is_important', 'created_at'
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications.
    """
    class Meta:
        model = Notification
        fields = [
            'user', 'notification_type', 'title', 'message', 'priority',
            'is_important', 'referral', 'candidate', 'appointment'
        ]
    
    def create(self, validated_data):
        """Create notification and send it."""
        from .services import NotificationService
        
        notification = super().create(validated_data)
        
        # Send notification
        service = NotificationService()
        service._send_notification(notification)
        
        return notification


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationTemplate model.
    """
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'title_template', 'message_template',
            'email_subject_template', 'email_body_template', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_notification_type(self, value):
        """Validate notification type."""
        valid_types = [choice[0] for choice in Notification.NotificationType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid notification type. Must be one of: {valid_types}")
        return value


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'referral_update_method', 'matching_complete_method', 'invitation_method',
            'response_method', 'appointment_method', 'system_method', 'reminder_method',
            'email_notifications_enabled', 'push_notifications_enabled',
            'quiet_hours_start', 'quiet_hours_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_delivery_method(self, value, field_name):
        """Validate delivery method."""
        valid_methods = [choice[0] for choice in NotificationPreference.DeliveryMethod.choices]
        if value not in valid_methods:
            raise serializers.ValidationError(f"Invalid delivery method for {field_name}. Must be one of: {valid_methods}")
        return value
    
    def validate_referral_update_method(self, value):
        return self.validate_delivery_method(value, 'referral_update_method')
    
    def validate_matching_complete_method(self, value):
        return self.validate_delivery_method(value, 'matching_complete_method')
    
    def validate_invitation_method(self, value):
        return self.validate_delivery_method(value, 'invitation_method')
    
    def validate_response_method(self, value):
        return self.validate_delivery_method(value, 'response_method')
    
    def validate_appointment_method(self, value):
        return self.validate_delivery_method(value, 'appointment_method')
    
    def validate_system_method(self, value):
        return self.validate_delivery_method(value, 'system_method')
    
    def validate_reminder_method(self, value):
        return self.validate_delivery_method(value, 'reminder_method')
    
    def validate(self, data):
        """Validate quiet hours."""
        quiet_start = data.get('quiet_hours_start')
        quiet_end = data.get('quiet_hours_end')
        
        if quiet_start and quiet_end:
            if quiet_start == quiet_end:
                raise serializers.ValidationError("Quiet hours start and end cannot be the same time.")
        
        return data


class NotificationChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationChannel model.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'user', 'user_name', 'channel_name', 'is_active',
            'last_seen', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics.
    """
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    important = serializers.IntegerField()
    referral_update_unread = serializers.IntegerField()
    matching_complete_unread = serializers.IntegerField()
    invitation_unread = serializers.IntegerField()
    response_unread = serializers.IntegerField()
    appointment_unread = serializers.IntegerField()
    system_unread = serializers.IntegerField()
    reminder_unread = serializers.IntegerField()


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of notification IDs to mark as read"
    )
    
    def validate_notification_ids(self, value):
        """Validate that all notification IDs exist and belong to the user."""
        if not value:
            raise serializers.ValidationError("At least one notification ID is required.")
        
        # Check if all notifications exist and belong to the user
        user = self.context['request'].user
        existing_ids = set(
            Notification.objects.filter(
                id__in=value,
                user=user
            ).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(f"Notifications not found or access denied: {list(missing_ids)}")
        
        return value


class NotificationBulkActionSerializer(serializers.Serializer):
    """
    Serializer for bulk notification actions.
    """
    ACTION_CHOICES = [
        ('mark_read', 'Mark as Read'),
        ('mark_unread', 'Mark as Unread'),
        ('delete', 'Delete'),
        ('mark_important', 'Mark as Important'),
        ('unmark_important', 'Unmark as Important'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of notification IDs to perform action on"
    )
    
    def validate_notification_ids(self, value):
        """Validate that all notification IDs exist and belong to the user."""
        if not value:
            raise serializers.ValidationError("At least one notification ID is required.")
        
        # Check if all notifications exist and belong to the user
        user = self.context['request'].user
        existing_ids = set(
            Notification.objects.filter(
                id__in=value,
                user=user
            ).values_list('id', flat=True)
        )
        
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(f"Notifications not found or access denied: {list(missing_ids)}")
        
        return value
