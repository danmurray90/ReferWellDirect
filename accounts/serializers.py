"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Organisation, UserOrganisation, OnboardingStep, UserOnboardingProgress, OnboardingSession

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    full_name = serializers.ReadOnlyField()
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'user_type_display', 'phone', 'date_of_birth',
            'profile_picture', 'is_active', 'is_verified', 'preferred_language',
            'timezone', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    def validate_email(self, value):
        """
        Validate email uniqueness.
        """
        if self.instance and self.instance.email == value:
            return value
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class OrganisationSerializer(serializers.ModelSerializer):
    """
    Serializer for Organisation model.
    """
    organisation_type_display = serializers.CharField(source='get_organisation_type_display', read_only=True)
    location_lat = serializers.SerializerMethodField()
    location_lon = serializers.SerializerMethodField()
    
    class Meta:
        model = Organisation
        fields = [
            'id', 'name', 'organisation_type', 'organisation_type_display',
            'email', 'phone', 'website', 'address_line_1', 'address_line_2',
            'city', 'postcode', 'country', 'location', 'location_lat', 'location_lon',
            'ods_code', 'ccg_code', 'is_active', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_location_lat(self, obj):
        """
        Get latitude from location point.
        """
        if obj.location:
            return obj.location.y
        return None
    
    def get_location_lon(self, obj):
        """
        Get longitude from location point.
        """
        if obj.location:
            return obj.location.x
        return None
    
    def validate_ods_code(self, value):
        """
        Validate ODS code format.
        """
        if value and len(value) != 5:
            raise serializers.ValidationError("ODS code must be exactly 5 characters.")
        return value
    
    def validate_ccg_code(self, value):
        """
        Validate CCG code format.
        """
        if value and len(value) != 3:
            raise serializers.ValidationError("CCG code must be exactly 3 characters.")
        return value


class UserOrganisationSerializer(serializers.ModelSerializer):
    """
    Serializer for UserOrganisation model.
    """
    user = UserSerializer(read_only=True)
    organisation = OrganisationSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    organisation_id = serializers.UUIDField(write_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserOrganisation
        fields = [
            'id', 'user', 'organisation', 'user_id', 'organisation_id',
            'role', 'role_display', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate user and organisation exist and relationship is unique.
        """
        user_id = data.get('user_id')
        organisation_id = data.get('organisation_id')
        
        if user_id and organisation_id:
            # Check if relationship already exists
            if UserOrganisation.objects.filter(
                user_id=user_id,
                organisation_id=organisation_id
            ).exists():
                raise serializers.ValidationError(
                    "This user is already associated with this organisation."
                )
        
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile updates.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'date_of_birth',
            'profile_picture', 'preferred_language', 'timezone'
        ]
    
    def validate_phone(self, value):
        """
        Validate phone number format.
        """
        if value and not value.startswith('+'):
            # Add UK country code if not present
            if value.startswith('0'):
                value = '+44' + value[1:]
            else:
                value = '+44' + value
        return value


class OrganisationProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for organisation profile updates.
    """
    class Meta:
        model = Organisation
        fields = [
            'name', 'email', 'phone', 'website', 'address_line_1',
            'address_line_2', 'city', 'postcode', 'country'
        ]


class OnboardingStepSerializer(serializers.ModelSerializer):
    """
    Serializer for OnboardingStep model.
    """
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = OnboardingStep
        fields = [
            'id', 'name', 'step_type', 'step_type_display', 'user_type', 'user_type_display',
            'order', 'is_required', 'description', 'help_text', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserOnboardingProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for UserOnboardingProgress model.
    """
    step = OnboardingStepSerializer(read_only=True)
    step_id = serializers.UUIDField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_completed = serializers.ReadOnlyField()
    is_skipped = serializers.ReadOnlyField()
    
    class Meta:
        model = UserOnboardingProgress
        fields = [
            'id', 'step', 'step_id', 'status', 'status_display',
            'started_at', 'completed_at', 'data', 'is_completed', 'is_skipped',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'created_at', 'updated_at']
    
    def validate_step_id(self, value):
        """
        Validate that the step exists and is active.
        """
        try:
            step = OnboardingStep.objects.get(id=value, is_active=True)
        except OnboardingStep.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive step.")
        return value


class OnboardingSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for OnboardingSession model.
    """
    user = UserSerializer(read_only=True)
    current_step = OnboardingStepSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = OnboardingSession
        fields = [
            'id', 'user', 'status', 'status_display', 'current_step',
            'started_at', 'completed_at', 'last_activity', 'session_data',
            'progress_percentage', 'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'last_activity', 'created_at', 'updated_at']


class OnboardingStepDataSerializer(serializers.Serializer):
    """
    Serializer for step-specific data validation.
    """
    def validate(self, data):
        """
        Validate step data based on step type.
        """
        step_type = self.context.get('step_type')
        
        if step_type == OnboardingStep.StepType.PROFILE_SETUP:
            required_fields = ['first_name', 'last_name', 'phone']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError(f"{field} is required for profile setup.")
        
        elif step_type == OnboardingStep.StepType.ORGANISATION_SETUP:
            required_fields = ['organisation_name', 'organisation_type']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError(f"{field} is required for organisation setup.")
        
        elif step_type == OnboardingStep.StepType.PREFERENCES:
            # Preferences are optional but validate if provided
            valid_preferences = ['preferred_language', 'timezone', 'notification_preferences']
            for key in data.keys():
                if key not in valid_preferences:
                    raise serializers.ValidationError(f"Invalid preference: {key}")
        
        return data


class OnboardingProgressUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating onboarding progress.
    """
    step_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=['start', 'complete', 'skip'])
    data = serializers.JSONField(required=False, default=dict)
    
    def validate_step_id(self, value):
        """
        Validate that the step exists and is active.
        """
        try:
            step = OnboardingStep.objects.get(id=value, is_active=True)
        except OnboardingStep.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive step.")
        return value
    
    def validate(self, data):
        """
        Validate the action and data combination.
        """
        action = data.get('action')
        step_data = data.get('data', {})
        
        if action == 'complete' and not step_data:
            # Some steps might require data to complete
            step_id = data.get('step_id')
            try:
                step = OnboardingStep.objects.get(id=step_id)
                if step.step_type in [OnboardingStep.StepType.PROFILE_SETUP, OnboardingStep.StepType.ORGANISATION_SETUP]:
                    raise serializers.ValidationError("This step requires data to complete.")
            except OnboardingStep.DoesNotExist:
                pass
        
        return data
