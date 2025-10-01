"""
Inbox views for ReferWell Direct.
"""
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView, TemplateView

from .models import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationTemplate,
)
from .serializers import (
    NotificationBulkActionSerializer,
    NotificationChannelSerializer,
    NotificationCreateSerializer,
    NotificationListSerializer,
    NotificationMarkReadSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
    NotificationStatsSerializer,
    NotificationTemplateSerializer,
)
from .services import NotificationChannelService, NotificationService


class NotificationPagination(PageNumberPagination):
    """Custom pagination for notifications."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@login_required
def inbox_dashboard(request):
    """
    Inbox dashboard view.
    """
    service = NotificationService()
    stats = service.get_notification_stats(request.user)

    context = {
        "user": request.user,
        "notifications": Notification.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:10],
        "stats": stats,
    }
    return render(request, "inbox/dashboard.html", context)


class NotificationViewSet(ModelViewSet):
    """
    ViewSet for notification operations.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        """Get notifications for the authenticated user."""
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")

        # Filter by notification type
        notification_type = self.request.query_params.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by priority
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by important status
        is_important = self.request.query_params.get("is_important")
        if is_important is not None:
            queryset = queryset.filter(is_important=is_important.lower() == "true")

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return NotificationListSerializer
        elif self.action == "create":
            return NotificationCreateSerializer
        return NotificationSerializer

    def perform_create(self, serializer):
        """Create notification for the authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get notification statistics for the user."""
        service = NotificationService()
        stats = service.get_notification_stats(request.user)
        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_read(self, request):
        """Mark multiple notifications as read."""
        serializer = NotificationMarkReadSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            notification_ids = serializer.validated_data["notification_ids"]
            service = NotificationService()

            success_count = 0
            for notification_id in notification_ids:
                if service.mark_as_read(str(notification_id), request.user):
                    success_count += 1

            return Response(
                {
                    "message": f"Marked {success_count} notifications as read",
                    "success_count": success_count,
                    "total_count": len(notification_ids),
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on notifications."""
        serializer = NotificationBulkActionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            action = serializer.validated_data["action"]
            notification_ids = serializer.validated_data["notification_ids"]

            notifications = Notification.objects.filter(
                id__in=notification_ids, user=request.user
            )

            success_count = 0
            if action == "mark_read":
                notifications.update(is_read=True)
                success_count = notifications.count()
            elif action == "mark_unread":
                notifications.update(is_read=False)
                success_count = notifications.count()
            elif action == "delete":
                success_count = notifications.count()
                notifications.delete()
            elif action == "mark_important":
                notifications.update(is_important=True)
                success_count = notifications.count()
            elif action == "unmark_important":
                notifications.update(is_important=False)
                success_count = notifications.count()

            return Response(
                {
                    "message": f'Bulk action "{action}" completed successfully',
                    "success_count": success_count,
                    "total_count": len(notification_ids),
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark a specific notification as read."""
        notification = self.get_object()
        service = NotificationService()

        if service.mark_as_read(str(notification.id), request.user):
            return Response({"message": "Notification marked as read"})

        return Response(
            {"error": "Failed to mark notification as read"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class NotificationTemplateViewSet(ModelViewSet):
    """
    ViewSet for notification template operations.
    """

    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter templates by notification type if specified."""
        queryset = super().get_queryset()
        notification_type = self.request.query_params.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        return queryset.filter(is_active=True)


class NotificationPreferenceViewSet(ModelViewSet):
    """
    ViewSet for notification preference operations.
    """

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get preferences for the authenticated user."""
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create preferences for the authenticated user."""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj

    def list(self, request, *args, **kwargs):
        """Return the user's preferences (create if not exist)."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create preferences for the authenticated user."""
        serializer.save(user=self.request.user)


class NotificationChannelViewSet(ModelViewSet):
    """
    ViewSet for notification channel operations.
    """

    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get channels for the authenticated user."""
        return NotificationChannel.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create channel for the authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a notification channel."""
        channel = self.get_object()
        service = NotificationChannelService()

        if service.deactivate_channel(channel.channel_name):
            return Response({"message": "Channel deactivated successfully"})

        return Response(
            {"error": "Failed to deactivate channel"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Legacy API views for backward compatibility
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    API view to list notifications for the authenticated user.
    """
    service = NotificationService()
    unread_only = request.query_params.get("unread_only", "false").lower() == "true"
    notification_type = request.query_params.get("notification_type")
    limit = int(request.query_params.get("limit", 50))
    offset = int(request.query_params.get("offset", 0))

    notifications = service.get_user_notifications(
        user=request.user,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        offset=offset,
    )

    serializer = NotificationListSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_detail(request, notification_id):
    """
    API view to get a specific notification.
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    API view to mark a notification as read.
    """
    service = NotificationService()

    if service.mark_as_read(notification_id, request.user):
        return Response({"message": "Notification marked as read"})

    return Response(
        {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_stats(request):
    """
    API view to get notification statistics.
    """
    service = NotificationService()
    stats = service.get_notification_stats(request.user)
    serializer = NotificationStatsSerializer(stats)
    return Response(serializer.data)


# Template views for web interface
class InboxView(LoginRequiredMixin, TemplateView):
    """
    Main inbox view.
    """

    template_name = "inbox/inbox.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get unread notifications
        context["unread_notifications"] = Notification.objects.filter(
            user=user, is_read=False
        ).order_by("-created_at")[:10]

        # Get recent notifications
        context["recent_notifications"] = Notification.objects.filter(
            user=user
        ).order_by("-created_at")[:20]

        # Get notification stats
        service = NotificationService()
        context["stats"] = service.get_notification_stats(user)

        return context


class NotificationListView(LoginRequiredMixin, ListView):
    """
    List view for notifications.
    """

    model = Notification
    template_name = "inbox/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a specific notification.
    """

    model = Notification
    template_name = "inbox/notification_detail.html"
    context_object_name = "notification"

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark notification as read when viewed
        notification = self.get_object()
        notification.mark_as_read()
        return response
