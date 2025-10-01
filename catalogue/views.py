"""
Views for catalogue app.
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from .models import Availability, Psychologist, Qualification, Review, Specialism
from .serializers import (
    AvailabilitySerializer,
    PsychologistSerializer,
    QualificationSerializer,
    ReviewSerializer,
    SpecialismSerializer,
)


class PsychologistListView(LoginRequiredMixin, ListView):
    """
    List view for psychologists.
    """

    model = Psychologist
    template_name = "catalogue/psychologist_list.html"
    context_object_name = "psychologists"
    paginate_by = 20

    def get_queryset(self):
        queryset = Psychologist.objects.filter(
            is_active=True, is_accepting_referrals=True
        )

        # Filter by service type
        service_type = self.request.GET.get("service_type")
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        # Filter by modality
        modality = self.request.GET.get("modality")
        if modality:
            queryset = queryset.filter(modality=modality)

        # Filter by specialism
        specialism = self.request.GET.get("specialism")
        if specialism:
            queryset = queryset.filter(specialisms__contains=[specialism])

        # Filter by language
        language = self.request.GET.get("language")
        if language:
            queryset = queryset.filter(languages__contains=[language])

        # Filter by location (if provided)
        lat = self.request.GET.get("lat")
        lon = self.request.GET.get("lon")
        radius_km = self.request.GET.get("radius_km", 50)

        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)
                queryset = (
                    queryset.filter(
                        location__distance_lte=(user_location, float(radius_km) * 1000)
                    )
                    .distance(user_location)
                    .order_by("distance")
                )
            except (ValueError, TypeError):
                pass

        return queryset.select_related("user")


class PsychologistDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a specific psychologist.
    """

    model = Psychologist
    template_name = "catalogue/psychologist_detail.html"
    context_object_name = "psychologist"

    def get_queryset(self):
        return Psychologist.objects.filter(is_active=True).select_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        psychologist = self.get_object()
        context["availabilities"] = psychologist.availabilities.filter(
            is_active=True
        ).order_by("day_of_week", "start_time")
        context["reviews"] = psychologist.reviews.filter(is_public=True).order_by(
            "-created_at"
        )[:10]
        return context


class PsychologistDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view for psychologists.
    """

    template_name = "catalogue/psychologist_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_psychologist and hasattr(user, "psychologist_profile"):
            psychologist = user.psychologist_profile
            context["psychologist"] = psychologist
            context["availabilities"] = psychologist.availabilities.filter(
                is_active=True
            ).order_by("day_of_week", "start_time")
            context["recent_reviews"] = psychologist.reviews.filter(
                is_public=True
            ).order_by("-created_at")[:5]
            context[
                "upcoming_appointments"
            ] = psychologist.appointments_as_psychologist.filter(
                status__in=["scheduled", "confirmed"]
            ).order_by(
                "scheduled_at"
            )[
                :5
            ]

        return context


# API Views
class PsychologistListAPIView(generics.ListAPIView):
    """
    API view for listing psychologists.
    """

    serializer_class = PsychologistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Psychologist.objects.filter(
            is_active=True, is_accepting_referrals=True
        )

        # Apply filters
        service_type = self.request.query_params.get("service_type")
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        modality = self.request.query_params.get("modality")
        if modality:
            queryset = queryset.filter(modality=modality)

        specialism = self.request.query_params.get("specialism")
        if specialism:
            queryset = queryset.filter(specialisms__contains=[specialism])

        language = self.request.query_params.get("language")
        if language:
            queryset = queryset.filter(languages__contains=[language])

        # Location filtering
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        radius_km = self.request.query_params.get("radius_km", 50)

        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)
                queryset = (
                    queryset.filter(
                        location__distance_lte=(user_location, float(radius_km) * 1000)
                    )
                    .distance(user_location)
                    .order_by("distance")
                )
            except (ValueError, TypeError):
                pass

        return queryset.select_related("user")


class PsychologistDetailAPIView(generics.RetrieveAPIView):
    """
    API view for retrieving a specific psychologist.
    """

    serializer_class = PsychologistSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Psychologist.objects.filter(is_active=True).select_related("user")


class AvailabilityListAPIView(generics.ListAPIView):
    """
    API view for listing psychologist availabilities.
    """

    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        psychologist_id = self.kwargs.get("psychologist_id")
        return Availability.objects.filter(
            psychologist_id=psychologist_id, is_active=True
        ).order_by("day_of_week", "start_time")


class SpecialismListAPIView(generics.ListAPIView):
    """
    API view for listing specialisms.
    """

    serializer_class = SpecialismSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Specialism.objects.filter(is_active=True).order_by("name")


class QualificationListAPIView(generics.ListAPIView):
    """
    API view for listing qualifications.
    """

    serializer_class = QualificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Qualification.objects.filter(is_active=True).order_by("name")


class ReviewListAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating reviews.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        psychologist_id = self.kwargs.get("psychologist_id")
        return Review.objects.filter(
            psychologist_id=psychologist_id, is_public=True
        ).order_by("-created_at")

    def perform_create(self, serializer):
        psychologist_id = self.kwargs.get("psychologist_id")
        psychologist = get_object_or_404(Psychologist, id=psychologist_id)
        serializer.save(patient=self.request.user, psychologist=psychologist)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_psychologist_availability(request, psychologist_id):
    """
    API endpoint to update psychologist availability.
    """
    try:
        psychologist = Psychologist.objects.get(id=psychologist_id)

        # Check permissions
        if psychologist.user != request.user and not request.user.is_admin:
            return Response(
                {"error": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN
            )

        # Update availability status
        availability_status = request.data.get("availability_status")
        if availability_status:
            psychologist.availability_status = availability_status

        # Update other fields
        is_accepting_referrals = request.data.get("is_accepting_referrals")
        if is_accepting_referrals is not None:
            psychologist.is_accepting_referrals = is_accepting_referrals

        max_patients = request.data.get("max_patients")
        if max_patients is not None:
            psychologist.max_patients = max_patients

        psychologist.save()

        return Response(
            {"message": "Availability updated successfully"}, status=status.HTTP_200_OK
        )

    except Psychologist.DoesNotExist:
        return Response(
            {"error": "Psychologist not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_availability_slot(request, psychologist_id):
    """
    API endpoint to add a new availability slot.
    """
    try:
        psychologist = Psychologist.objects.get(id=psychologist_id)

        # Check permissions
        if psychologist.user != request.user and not request.user.is_admin:
            return Response(
                {"error": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN
            )

        # Create availability slot
        availability_data = {
            "psychologist": psychologist,
            "day_of_week": request.data.get("day_of_week"),
            "start_time": request.data.get("start_time"),
            "end_time": request.data.get("end_time"),
            "modality": request.data.get("modality", psychologist.modality),
        }

        availability = Availability.objects.create(**availability_data)
        serializer = AvailabilitySerializer(availability)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Psychologist.DoesNotExist:
        return Response(
            {"error": "Psychologist not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
