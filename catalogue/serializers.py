"""
Serializers for catalogue app.
"""
from rest_framework import serializers

from django.contrib.auth import get_user_model

from .models import Availability, Psychologist, Qualification, Review, Specialism

User = get_user_model()


class PsychologistSerializer(serializers.ModelSerializer):
    """
    Serializer for Psychologist model.
    """

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    service_type_display = serializers.CharField(
        source="get_service_type_display", read_only=True
    )
    modality_display = serializers.CharField(
        source="get_modality_display", read_only=True
    )
    availability_status_display = serializers.CharField(
        source="get_availability_status_display", read_only=True
    )
    location_lat = serializers.SerializerMethodField()
    location_lon = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Psychologist
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "title",
            "qualifications",
            "specialisms",
            "languages",
            "service_type",
            "service_type_display",
            "modality",
            "modality_display",
            "location",
            "location_lat",
            "location_lon",
            "address_line_1",
            "address_line_2",
            "city",
            "postcode",
            "country",
            "registration_number",
            "registration_body",
            "years_experience",
            "availability_status",
            "availability_status_display",
            "max_patients",
            "current_patients",
            "hourly_rate",
            "session_duration",
            "preferred_age_groups",
            "preferred_conditions",
            "max_distance_km",
            "is_verified",
            "is_active",
            "is_accepting_referrals",
            "capacity_available",
            "is_available",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
            "last_updated_embedding",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_updated_embedding"]

    def get_location_lat(self, obj):
        """Get latitude from location point."""
        if obj.location:
            return obj.location.y
        return None

    def get_location_lon(self, obj):
        """Get longitude from location point."""
        if obj.location:
            return obj.location.x
        return None

    def get_average_rating(self, obj):
        """Calculate average rating from reviews."""
        reviews = obj.reviews.filter(is_public=True)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return None

    def get_review_count(self, obj):
        """Get count of public reviews."""
        return obj.reviews.filter(is_public=True).count()


class AvailabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for Availability model.
    """

    psychologist_name = serializers.CharField(
        source="psychologist.user.get_full_name", read_only=True
    )
    day_of_week_display = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )
    modality_display = serializers.CharField(
        source="get_modality_display", read_only=True
    )

    class Meta:
        model = Availability
        fields = [
            "id",
            "psychologist",
            "psychologist_name",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "modality",
            "modality_display",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate availability slot."""
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("End time must be after start time.")

        return data


class SpecialismSerializer(serializers.ModelSerializer):
    """
    Serializer for Specialism model.
    """

    class Meta:
        model = Specialism
        fields = [
            "id",
            "name",
            "description",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        """Validate specialism name is unique."""
        if self.instance and self.instance.name == value:
            return value

        if Specialism.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                "A specialism with this name already exists."
            )
        return value


class QualificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Qualification model.
    """

    class Meta:
        model = Qualification
        fields = [
            "id",
            "name",
            "description",
            "abbreviation",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        """Validate qualification name is unique."""
        if self.instance and self.instance.name == value:
            return value

        if Qualification.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                "A qualification with this name already exists."
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    """

    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    psychologist_name = serializers.CharField(
        source="psychologist.user.get_full_name", read_only=True
    )
    rating_display = serializers.CharField(source="get_rating_display", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "psychologist",
            "psychologist_name",
            "patient",
            "patient_name",
            "rating",
            "rating_display",
            "title",
            "content",
            "is_verified",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_rating(self, value):
        """Validate rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_title(self, value):
        """Validate title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required.")
        return value

    def validate_content(self, value):
        """Validate content is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Content is required.")
        return value


class PsychologistProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating psychologist profile.
    """

    class Meta:
        model = Psychologist
        fields = [
            "title",
            "qualifications",
            "specialisms",
            "languages",
            "service_type",
            "modality",
            "address_line_1",
            "address_line_2",
            "city",
            "postcode",
            "country",
            "registration_number",
            "registration_body",
            "years_experience",
            "hourly_rate",
            "session_duration",
            "preferred_age_groups",
            "preferred_conditions",
            "max_distance_km",
        ]

    def validate_hourly_rate(self, value):
        """Validate hourly rate is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Hourly rate must be positive.")
        return value

    def validate_session_duration(self, value):
        """Validate session duration is reasonable."""
        if value < 15 or value > 480:  # 15 minutes to 8 hours
            raise serializers.ValidationError(
                "Session duration must be between 15 and 480 minutes."
            )
        return value

    def validate_years_experience(self, value):
        """Validate years of experience is reasonable."""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError(
                "Years of experience must be between 0 and 100."
            )
        return value


class PsychologistSearchSerializer(serializers.Serializer):
    """
    Serializer for psychologist search parameters.
    """

    service_type = serializers.ChoiceField(
        choices=Psychologist.ServiceType.choices, required=False
    )
    modality = serializers.ChoiceField(
        choices=Psychologist.Modality.choices, required=False
    )
    specialism = serializers.CharField(max_length=100, required=False)
    language = serializers.CharField(max_length=10, required=False)
    lat = serializers.FloatField(required=False)
    lon = serializers.FloatField(required=False)
    radius_km = serializers.FloatField(default=50, required=False)

    def validate_lat(self, value):
        """Validate latitude is within valid range."""
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_lon(self, value):
        """Validate longitude is within valid range."""
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def validate_radius_km(self, value):
        """Validate radius is reasonable."""
        if value < 1 or value > 1000:
            raise serializers.ValidationError("Radius must be between 1 and 1000 km.")
        return value
