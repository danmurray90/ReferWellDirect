"""
Views for referrals app.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, TemplateView, UpdateView

from .bulk_operations_service import (
    AppointmentBulkOperationsService,
    TaskBulkOperationsService,
)
from .forms import ReferralForm
from .models import Appointment, Candidate, Referral, Task
from .search_service import AdvancedSearchService, BulkOperationsService
from .serializers import CandidateSerializer, ReferralSerializer


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view.
    """

    template_name = "referrals/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_gp:
            referrals = Referral.objects.filter(referrer=user)
            context["referrals"] = referrals.order_by("-created_at")[:10]
            context["pending_tasks"] = Task.objects.filter(
                assigned_to=user, is_completed=False
            ).order_by("-due_at")[:5]
        elif user.is_patient:
            referrals = Referral.objects.filter(patient=user)
            context["referrals"] = referrals.order_by("-created_at")[:10]
            context["upcoming_appointments"] = Appointment.objects.filter(
                patient=user,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
            ).order_by("scheduled_at")[:5]
        elif user.is_psychologist:
            context["candidates"] = Candidate.objects.filter(
                psychologist=user
            ).order_by("-created_at")[:10]
            context["upcoming_appointments"] = Appointment.objects.filter(
                psychologist=user,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
            ).order_by("scheduled_at")[:5]
            referrals = (
                Referral.objects.none()
            )  # Psychologists don't see referrals directly
        elif user.is_admin:
            referrals = Referral.objects.all()
            context["recent_referrals"] = referrals.order_by("-created_at")[:10]
            context["pending_tasks"] = Task.objects.filter(is_completed=False).order_by(
                "-due_at"
            )[:10]
        else:
            referrals = Referral.objects.none()

        # Add statistics for all user types
        if "referrals" in context:
            context["total_referrals"] = referrals.count()
            context["active_referrals"] = referrals.exclude(
                status__in=[
                    Referral.Status.COMPLETED,
                    Referral.Status.CANCELLED,
                    Referral.Status.REJECTED,
                ]
            ).count()
            context["completed_referrals"] = referrals.filter(
                status=Referral.Status.COMPLETED
            ).count()
        else:
            context["total_referrals"] = 0
            context["active_referrals"] = 0
            context["completed_referrals"] = 0

        return context


class CreateReferralView(LoginRequiredMixin, TemplateView):
    """
    Create referral form view.
    """

    template_name = "referrals/create_referral.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ReferralForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = ReferralForm(request.POST, user=request.user)

        if form.is_valid():
            try:
                referral = form.save(commit=False)
                referral.referrer = request.user
                referral.created_by = request.user
                referral.save()
                messages.success(
                    request, f"Referral {referral.referral_id} created successfully!"
                )
                return redirect("referrals:referral_detail", pk=referral.pk)
            except Exception as e:
                messages.error(request, f"Error creating referral: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")

        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


class ReferralListView(LoginRequiredMixin, TemplateView):
    """
    Enhanced list view for referrals with advanced search and filtering.
    """

    template_name = "referrals/referral_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get search parameters
        search_params = self._get_search_params()

        # Perform search
        search_service = AdvancedSearchService()
        referrals, metadata = search_service.search_referrals(
            user=self.request.user,
            search_params=search_params,
            page=search_params.get("page", 1),
            page_size=search_params.get("page_size", 20),
        )

        # Get search facets
        facets = search_service.get_search_facets(self.request.user, search_params)

        # Get search analytics
        analytics = search_service.get_search_analytics(
            self.request.user, search_params
        )

        context.update(
            {
                "referrals": referrals,
                "metadata": metadata,
                "facets": facets,
                "analytics": analytics,
                "search_params": search_params,
                "status_choices": Referral.Status.choices,
                "priority_choices": Referral.Priority.choices,
                "service_type_choices": Referral.ServiceType.choices,
                "modality_choices": Referral.Modality.choices,
            }
        )

        return context

    def _get_search_params(self):
        """Extract search parameters from request."""
        params = {}

        # Text search
        if self.request.GET.get("q"):
            params["q"] = self.request.GET.get("q")

        # Basic filters
        for field in [
            "status",
            "priority",
            "service_type",
            "modality",
            "patient_age_group",
            "preferred_language",
        ]:
            if self.request.GET.get(field):
                params[field] = self.request.GET.get(field)

        # Date filters
        for field in ["created_from", "created_to", "submitted_from", "submitted_to"]:
            if self.request.GET.get(field):
                try:
                    params[field] = timezone.datetime.strptime(
                        self.request.GET.get(field), "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

        # Specialism filters
        if self.request.GET.get("required_specialisms"):
            specialisms = self.request.GET.getlist("required_specialisms")
            params["required_specialisms"] = specialisms

        # Numeric filters
        for field in [
            "max_distance_km",
            "min_candidates",
            "max_candidates",
            "min_score",
            "max_score",
        ]:
            if self.request.GET.get(field):
                try:
                    params[field] = float(self.request.GET.get(field))
                except ValueError:
                    pass

        # Boolean filters
        for field in ["has_candidates", "has_appointments"]:
            if self.request.GET.get(field):
                params[field] = self.request.GET.get(field).lower() == "true"

        # Pagination
        try:
            params["page"] = int(self.request.GET.get("page", 1))
        except ValueError:
            params["page"] = 1

        try:
            params["page_size"] = int(self.request.GET.get("page_size", 20))
        except ValueError:
            params["page_size"] = 20

        # Sorting
        if self.request.GET.get("sort"):
            params["sort"] = self.request.GET.get("sort")

        return params


class ReferralDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a specific referral.
    """

    model = Referral
    template_name = "referrals/referral_detail.html"
    context_object_name = "referral"

    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_patient:
            return Referral.objects.filter(patient=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral = self.get_object()
        context["candidates"] = referral.candidates.all().order_by("-final_score")
        context["appointments"] = referral.appointments.all().order_by("-scheduled_at")
        context["messages"] = referral.messages.all().order_by("-created_at")
        return context


class EditReferralView(LoginRequiredMixin, UpdateView):
    """
    Edit referral view.
    """

    model = Referral
    template_name = "referrals/edit_referral.html"
    fields = [
        "presenting_problem",
        "clinical_notes",
        "urgency_notes",
        "service_type",
        "modality",
        "priority",
        "patient_preferences",
        "preferred_latitude",
        "preferred_longitude",
        "max_distance_km",
        "preferred_language",
        "required_specialisms",
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()

    def get_success_url(self):
        return reverse("referrals:referral_detail", kwargs={"pk": self.object.pk})


class ShortlistView(LoginRequiredMixin, TemplateView):
    """
    Shortlist view for referral candidates.
    """

    template_name = "referrals/shortlist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral_id = self.kwargs.get("referral_id")
        referral = get_object_or_404(Referral, id=referral_id)

        # Check permissions
        user = self.request.user
        if not (user.is_gp and referral.referrer == user) and not user.is_admin:
            raise PermissionDenied

        context["referral"] = referral
        context["candidates"] = referral.candidates.filter(
            status__in=[Candidate.Status.SHORTLISTED, Candidate.Status.INVITED]
        ).order_by("-final_score")

        return context


# API Views
@extend_schema_view(
    get=extend_schema(
        summary="List referrals",
        description="Retrieve a list of referrals based on user permissions",
        tags=["Referrals"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by referral status",
                enum=[
                    "draft",
                    "submitted",
                    "matching",
                    "shortlisted",
                    "high_touch_queue",
                    "completed",
                    "cancelled",
                    "rejected",
                ],
            ),
            OpenApiParameter(
                name="priority",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by priority level",
                enum=["urgent", "high", "medium", "low"],
            ),
            OpenApiParameter(
                name="service_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by service type",
                enum=["nhs", "private", "mixed"],
            ),
        ],
    ),
    post=extend_schema(
        summary="Create referral",
        description="Create a new referral",
        tags=["Referrals"],
        examples=[
            OpenApiExample(
                "Example referral",
                summary="Basic referral creation",
                description="Example of creating a new referral",
                value={
                    "patient": "uuid-of-patient",
                    "presenting_problem": "Patient presenting with anxiety and depression",
                    "condition_description": "Generalized anxiety disorder with depressive symptoms",
                    "clinical_notes": "Patient has been experiencing symptoms for 6 months",
                    "service_type": "nhs",
                    "modality": "mixed",
                    "priority": "medium",
                    "preferred_language": "en",
                    "max_distance_km": 50,
                },
            )
        ],
    ),
)
class ReferralListAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating referrals.
    """

    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_patient:
            return Referral.objects.filter(patient=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()

    def perform_create(self, serializer):
        serializer.save(referrer=self.request.user, created_by=self.request.user)


class ReferralDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific referral.
    """

    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_patient:
            return Referral.objects.filter(patient=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()


class CandidateListAPIView(generics.ListAPIView):
    """
    API view for listing candidates for a referral.
    """

    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        referral_id = self.kwargs.get("referral_id")
        return Candidate.objects.filter(referral_id=referral_id).order_by(
            "-final_score"
        )


class CandidateDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating a specific candidate.
    """

    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Candidate.objects.all()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_referral(request, referral_id):
    """
    API endpoint to submit a referral for matching.
    """
    try:
        referral = Referral.objects.get(id=referral_id)

        # Check permissions
        if (
            not (request.user.is_gp and referral.referrer == request.user)
            and not request.user.is_admin
        ):
            return Response(
                {"error": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN
            )

        if referral.status != Referral.Status.DRAFT:
            return Response(
                {"error": "Referral is not in draft status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status
        referral.status = Referral.Status.SUBMITTED
        from django.utils import timezone

        referral.submitted_at = timezone.now()
        referral.save()

        # Trigger matching process (placeholder)
        # This would typically trigger a Celery task

        return Response(
            {"message": "Referral submitted successfully"}, status=status.HTTP_200_OK
        )

    except Referral.DoesNotExist:
        return Response(
            {"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def respond_to_invitation(request, candidate_id):
    """
    API endpoint for psychologists to respond to invitations.
    """
    try:
        candidate = Candidate.objects.get(id=candidate_id)

        # Check permissions
        if candidate.psychologist != request.user:
            return Response(
                {"error": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN
            )

        if candidate.status != Candidate.Status.INVITED:
            return Response(
                {"error": "Candidate is not in invited status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = request.data.get("response")  # 'accepted' or 'declined'
        notes = request.data.get("notes", "")

        if response == "accepted":
            candidate.status = Candidate.Status.ACCEPTED
        elif response == "declined":
            candidate.status = Candidate.Status.DECLINED
        else:
            return Response(
                {"error": "Invalid response"}, status=status.HTTP_400_BAD_REQUEST
            )

        candidate.response_notes = notes
        from django.utils import timezone

        candidate.responded_at = timezone.now()
        candidate.save()

        return Response(
            {"message": "Response recorded successfully"}, status=status.HTTP_200_OK
        )

    except Candidate.DoesNotExist:
        return Response(
            {"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Advanced Search API Views
@extend_schema(
    summary="Get search suggestions",
    description="Get search suggestions based on query text for autocomplete functionality",
    tags=["Search"],
    parameters=[
        OpenApiParameter(
            name="q",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Search query text",
            required=True,
            examples=[
                OpenApiExample("Anxiety", value="anxiety"),
                OpenApiExample("Depression", value="depression"),
                OpenApiExample("CBT", value="cbt"),
            ],
        ),
        OpenApiParameter(
            name="limit",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Maximum number of suggestions to return",
            default=10,
        ),
    ],
    responses={
        200: {
            "description": "Search suggestions",
            "examples": {
                "application/json": {
                    "suggestions": [
                        "anxiety and depression",
                        "anxiety management techniques",
                        "anxiety cognitive behavioral therapy",
                    ]
                }
            },
        },
        400: {
            "description": "Bad request",
            "examples": {"application/json": {"error": "Invalid query parameter"}},
        },
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_suggestions(request):
    """
    API endpoint for search suggestions.
    """
    try:
        query = request.GET.get("q", "")
        limit = int(request.GET.get("limit", 10))

        search_service = AdvancedSearchService()
        suggestions = search_service.get_search_suggestions(
            user=request.user, query=query, limit=limit
        )

        return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_facets(request):
    """
    API endpoint for search facets.
    """
    try:
        # Get search parameters from request
        search_params = {}
        for field in [
            "status",
            "priority",
            "service_type",
            "modality",
            "patient_age_group",
            "preferred_language",
        ]:
            if request.GET.get(field):
                search_params[field] = request.GET.get(field)

        search_service = AdvancedSearchService()
        facets = search_service.get_search_facets(
            user=request.user, search_params=search_params
        )

        return Response({"facets": facets}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_analytics(request):
    """
    API endpoint for search analytics.
    """
    try:
        # Get search parameters from request
        search_params = {}
        for field in [
            "status",
            "priority",
            "service_type",
            "modality",
            "patient_age_group",
            "preferred_language",
        ]:
            if request.GET.get(field):
                search_params[field] = request.GET.get(field)

        search_service = AdvancedSearchService()
        analytics = search_service.get_search_analytics(
            user=request.user, search_params=search_params
        )

        return Response({"analytics": analytics}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Bulk Operations API Views
@extend_schema(
    summary="Bulk update referral status",
    description="Update the status of multiple referrals in a single operation",
    tags=["Bulk Operations"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "referral_ids": {
                    "type": "array",
                    "items": {"type": "string", "format": "uuid"},
                    "description": "List of referral IDs to update",
                    "example": [
                        "123e4567-e89b-12d3-a456-426614174000",
                        "123e4567-e89b-12d3-a456-426614174001",
                    ],
                },
                "new_status": {
                    "type": "string",
                    "enum": [
                        "draft",
                        "submitted",
                        "matching",
                        "shortlisted",
                        "high_touch_queue",
                        "completed",
                        "cancelled",
                        "rejected",
                    ],
                    "description": "New status to set for all referrals",
                    "example": "completed",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes about the status update",
                    "example": "Bulk status update - all referrals completed",
                },
            },
            "required": ["referral_ids", "new_status"],
        }
    },
    responses={
        200: {
            "description": "Bulk update completed successfully",
            "examples": {
                "application/json": {
                    "success": True,
                    "updated_count": 5,
                    "total_requested": 5,
                    "errors": [],
                }
            },
        },
        400: {
            "description": "Bad request",
            "examples": {
                "application/json": {
                    "success": False,
                    "error": "referral_ids and new_status are required",
                    "updated_count": 0,
                    "total_requested": 0,
                }
            },
        },
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_update_status(request):
    """
    API endpoint for bulk status updates.
    """
    try:
        referral_ids = request.data.get("referral_ids", [])
        new_status = request.data.get("new_status")
        notes = request.data.get("notes", "")

        if not referral_ids or not new_status:
            return Response(
                {"error": "referral_ids and new_status are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = BulkOperationsService()
        result = bulk_service.bulk_update_status(
            user=request.user,
            referral_ids=referral_ids,
            new_status=new_status,
            notes=notes,
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_assign_referrer(request):
    """
    API endpoint for bulk referrer assignment.
    """
    try:
        referral_ids = request.data.get("referral_ids", [])
        new_referrer_id = request.data.get("new_referrer_id")

        if not referral_ids or not new_referrer_id:
            return Response(
                {"error": "referral_ids and new_referrer_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = BulkOperationsService()
        result = bulk_service.bulk_assign_referrer(
            user=request.user,
            referral_ids=referral_ids,
            new_referrer_id=new_referrer_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_export(request):
    """
    API endpoint for bulk export.
    """
    try:
        referral_ids = request.data.get("referral_ids", [])
        export_format = request.data.get("format", "csv")

        if not referral_ids:
            return Response(
                {"error": "referral_ids are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = BulkOperationsService()
        result = bulk_service.bulk_export(
            user=request.user, referral_ids=referral_ids, format=export_format
        )

        if not result["success"]:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Return file as response
        response = HttpResponse(result["data"], content_type=result["content_type"])
        response["Content-Disposition"] = f'attachment; filename="{result["filename"]}"'
        return response

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Appointment Bulk Operations API Views
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_update_appointment_status(request):
    """
    API endpoint for bulk appointment status updates.
    """
    try:
        appointment_ids = request.data.get("appointment_ids", [])
        new_status = request.data.get("new_status")
        notes = request.data.get("notes", "")

        if not appointment_ids or not new_status:
            return Response(
                {"error": "appointment_ids and new_status are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = AppointmentBulkOperationsService()
        result = bulk_service.bulk_update_status(
            user=request.user,
            appointment_ids=appointment_ids,
            new_status=new_status,
            notes=notes,
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_reschedule_appointments(request):
    """
    API endpoint for bulk appointment rescheduling.
    """
    try:
        appointment_ids = request.data.get("appointment_ids", [])
        new_datetime = request.data.get("new_datetime")
        notes = request.data.get("notes", "")

        if not appointment_ids or not new_datetime:
            return Response(
                {"error": "appointment_ids and new_datetime are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = AppointmentBulkOperationsService()
        result = bulk_service.bulk_reschedule(
            user=request.user,
            appointment_ids=appointment_ids,
            new_datetime=new_datetime,
            notes=notes,
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_assign_psychologist(request):
    """
    API endpoint for bulk psychologist assignment.
    """
    try:
        appointment_ids = request.data.get("appointment_ids", [])
        new_psychologist_id = request.data.get("new_psychologist_id")

        if not appointment_ids or not new_psychologist_id:
            return Response(
                {"error": "appointment_ids and new_psychologist_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = AppointmentBulkOperationsService()
        result = bulk_service.bulk_assign_psychologist(
            user=request.user,
            appointment_ids=appointment_ids,
            new_psychologist_id=new_psychologist_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_export_appointments(request):
    """
    API endpoint for bulk appointment export.
    """
    try:
        appointment_ids = request.data.get("appointment_ids", [])
        export_format = request.data.get("format", "csv")

        if not appointment_ids:
            return Response(
                {"error": "appointment_ids are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = AppointmentBulkOperationsService()
        result = bulk_service.bulk_export(
            user=request.user, appointment_ids=appointment_ids, format=export_format
        )

        if not result["success"]:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Return file as response
        response = HttpResponse(result["data"], content_type=result["content_type"])
        response["Content-Disposition"] = f'attachment; filename="{result["filename"]}"'
        return response

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Task Bulk Operations API Views
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_update_task_status(request):
    """
    API endpoint for bulk task status updates.
    """
    try:
        task_ids = request.data.get("task_ids", [])
        new_status = request.data.get("new_status")
        notes = request.data.get("notes", "")

        if not task_ids or not new_status:
            return Response(
                {"error": "task_ids and new_status are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = TaskBulkOperationsService()
        result = bulk_service.bulk_update_status(
            user=request.user, task_ids=task_ids, new_status=new_status, notes=notes
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_assign_task_user(request):
    """
    API endpoint for bulk task user assignment.
    """
    try:
        task_ids = request.data.get("task_ids", [])
        new_user_id = request.data.get("new_user_id")

        if not task_ids or not new_user_id:
            return Response(
                {"error": "task_ids and new_user_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bulk_service = TaskBulkOperationsService()
        result = bulk_service.bulk_assign_user(
            user=request.user, task_ids=task_ids, new_user_id=new_user_id
        )

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Self-referral view

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods


@csrf_protect
@require_http_methods(["GET", "POST"])
def self_referral_start(request):
    """
    Patient self-referral start view.
    """
    if request.method == "POST":
        # Handle self-referral form
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        date_of_birth = request.POST.get("date_of_birth")

        # Referral details
        presenting_problem = request.POST.get("presenting_problem")
        service_type = request.POST.get("service_type")
        modality = request.POST.get("modality")
        preferred_language = request.POST.get("preferred_language")

        # Optional account creation
        create_account = request.POST.get("create_account") == "on"
        password = request.POST.get("password")

        if first_name and last_name and presenting_problem:
            try:
                from accounts.models import User

                from .models import PatientProfile

                # Create patient profile
                patient_profile = PatientProfile.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    date_of_birth=date_of_birth if date_of_birth else None,
                )

                # Create user account if requested
                user = None
                if create_account and email and password:
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        user_type=User.UserType.PATIENT,
                        is_verified=True,
                    )
                    patient_profile.link_to_user(user)

                # Create referral (will need a system referrer or handle differently)
                # For now, we will create a placeholder referral
                referral = Referral.objects.create(
                    referral_id=f"SRF{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    referrer=user if user else None,  # Self-referred
                    patient=user if user else None,
                    patient_profile=patient_profile if not user else None,
                    presenting_problem=presenting_problem,
                    service_type=service_type or Referral.ServiceType.NHS,
                    modality=modality or Referral.Modality.MIXED,
                    preferred_language=preferred_language or "en",
                    status=Referral.Status.SUBMITTED,
                )

                if user:
                    # Authenticate and login user
                    user = authenticate(request, username=email, password=password)
                    if user:
                        login(request, user)
                        messages.success(
                            request, "Self-referral submitted successfully!"
                        )
                        return redirect("referrals:dashboard")
                else:
                    messages.success(
                        request,
                        "Self-referral submitted successfully! You can create an account later to track your referral.",
                    )
                    return redirect("public:landing")

            except Exception as e:
                messages.error(request, f"Error submitting referral: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, "referrals/self_referral_start.html")
