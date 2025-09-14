"""
Serializers for referrals app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Referral, Candidate, Appointment, Message, Task

User = get_user_model()


class ReferralSerializer(serializers.ModelSerializer):
    """
    Serializer for Referral model.
    """
    referrer_name = serializers.CharField(source='referrer.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    modality_display = serializers.CharField(source='get_modality_display', read_only=True)
    
    class Meta:
        model = Referral
        fields = [
            'id', 'referral_id', 'referrer', 'referrer_name', 'patient', 'patient_name',
            'status', 'status_display', 'priority', 'priority_display',
            'service_type', 'service_type_display', 'modality', 'modality_display',
            'presenting_problem', 'clinical_notes', 'urgency_notes',
            'patient_preferences', 'preferred_location', 'max_distance_km',
            'preferred_language', 'required_specialisms',
            'created_at', 'updated_at', 'submitted_at', 'completed_at'
        ]
        read_only_fields = ['id', 'referral_id', 'created_at', 'updated_at', 'submitted_at', 'completed_at']
    
    def validate_presenting_problem(self, value):
        """
        Validate presenting problem is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Presenting problem is required.")
        return value
    
    def validate_max_distance_km(self, value):
        """
        Validate maximum distance is reasonable.
        """
        if value < 1 or value > 500:
            raise serializers.ValidationError("Maximum distance must be between 1 and 500 km.")
        return value


class CandidateSerializer(serializers.ModelSerializer):
    """
    Serializer for Candidate model.
    """
    psychologist_name = serializers.CharField(source='psychologist.get_full_name', read_only=True)
    psychologist_email = serializers.CharField(source='psychologist.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'referral', 'psychologist', 'psychologist_name', 'psychologist_email',
            'status', 'status_display', 'similarity_score', 'structured_score',
            'final_score', 'confidence_score', 'matching_explanation',
            'invited_at', 'responded_at', 'expires_at', 'response_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_confidence_score(self, value):
        """
        Validate confidence score is between 0 and 1.
        """
        if value is not None and (value < 0 or value > 1):
            raise serializers.ValidationError("Confidence score must be between 0 and 1.")
        return value


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    psychologist_name = serializers.CharField(source='psychologist.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    modality_display = serializers.CharField(source='get_modality_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'referral', 'patient', 'patient_name', 'psychologist', 'psychologist_name',
            'scheduled_at', 'duration_minutes', 'location', 'modality', 'modality_display',
            'status', 'status_display', 'notes', 'outcome_notes',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'confirmed_at', 'completed_at']
    
    def validate_scheduled_at(self, value):
        """
        Validate scheduled time is in the future.
        """
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value
    
    def validate_duration_minutes(self, value):
        """
        Validate duration is reasonable.
        """
        if value < 15 or value > 480:  # 15 minutes to 8 hours
            raise serializers.ValidationError("Duration must be between 15 and 480 minutes.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    """
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'referral', 'sender', 'sender_name', 'recipient', 'recipient_name',
            'message_type', 'message_type_display', 'subject', 'content',
            'is_read', 'is_important', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def validate_subject(self, value):
        """
        Validate subject is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Subject is required.")
        return value
    
    def validate_content(self, value):
        """
        Validate content is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Content is required.")
        return value


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    """
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'referral', 'assigned_to', 'assigned_to_name', 'created_by', 'created_by_name',
            'task_type', 'task_type_display', 'title', 'description', 'priority', 'priority_display',
            'is_completed', 'is_overdue', 'created_at', 'updated_at', 'due_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def validate_title(self, value):
        """
        Validate title is not empty.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required.")
        return value


class ReferralCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating referrals.
    """
    class Meta:
        model = Referral
        fields = [
            'patient', 'presenting_problem', 'clinical_notes', 'urgency_notes',
            'service_type', 'modality', 'priority', 'patient_preferences',
            'preferred_location', 'max_distance_km', 'preferred_language',
            'required_specialisms'
        ]
    
    def create(self, validated_data):
        """
        Create a new referral.
        """
        validated_data['referrer'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CandidateResponseSerializer(serializers.Serializer):
    """
    Serializer for candidate responses to invitations.
    """
    response = serializers.ChoiceField(choices=['accepted', 'declined'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_response(self, value):
        """
        Validate response choice.
        """
        if value not in ['accepted', 'declined']:
            raise serializers.ValidationError("Response must be 'accepted' or 'declined'.")
        return value
