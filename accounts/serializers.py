"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Organisation, UserOrganisation

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
