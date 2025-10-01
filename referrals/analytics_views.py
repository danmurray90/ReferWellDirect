"""
Analytics and reporting views for referrals app.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView

from .analytics_service import AnalyticsService


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """
    Analytics dashboard view.
    """

    template_name = "referrals/analytics_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get date range from request
        date_range = self.request.GET.get("date_range", "30d")

        # Get analytics data
        analytics_service = AnalyticsService()
        metrics = analytics_service.get_dashboard_metrics(
            user=self.request.user, date_range=date_range
        )

        context.update(
            {
                "metrics": metrics,
                "date_range": date_range,
                "date_range_options": [
                    {"value": "7d", "label": "Last 7 days"},
                    {"value": "30d", "label": "Last 30 days"},
                    {"value": "90d", "label": "Last 90 days"},
                    {"value": "1y", "label": "Last year"},
                ],
            }
        )

        return context


class ReferralAnalyticsView(LoginRequiredMixin, TemplateView):
    """
    Detailed referral analytics view.
    """

    template_name = "referrals/referral_analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filters from request
        filters = self._get_filters()

        # Get analytics data
        analytics_service = AnalyticsService()
        analytics = analytics_service.get_referral_analytics(
            user=self.request.user, filters=filters
        )

        context.update(
            {
                "analytics": analytics,
                "filters": filters,
            }
        )

        return context

    def _get_filters(self):
        """Extract filters from request."""
        filters = {}

        for field in [
            "status",
            "priority",
            "service_type",
            "modality",
            "date_from",
            "date_to",
        ]:
            if self.request.GET.get(field):
                filters[field] = self.request.GET.get(field)

        return filters


class AppointmentAnalyticsView(LoginRequiredMixin, TemplateView):
    """
    Detailed appointment analytics view.
    """

    template_name = "referrals/appointment_analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filters from request
        filters = self._get_filters()

        # Get analytics data
        analytics_service = AnalyticsService()
        analytics = analytics_service.get_appointment_analytics(
            user=self.request.user, filters=filters
        )

        context.update(
            {
                "analytics": analytics,
                "filters": filters,
            }
        )

        return context

    def _get_filters(self):
        """Extract filters from request."""
        filters = {}

        for field in ["status", "modality", "date_from", "date_to"]:
            if self.request.GET.get(field):
                filters[field] = self.request.GET.get(field)

        return filters


class PerformanceMetricsView(LoginRequiredMixin, TemplateView):
    """
    Performance metrics view.
    """

    template_name = "referrals/performance_metrics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filters from request
        filters = self._get_filters()

        # Get analytics data
        analytics_service = AnalyticsService()
        metrics = analytics_service.get_performance_metrics(
            user=self.request.user, filters=filters
        )

        context.update(
            {
                "metrics": metrics,
                "filters": filters,
            }
        )

        return context

    def _get_filters(self):
        """Extract filters from request."""
        filters = {}

        for field in ["date_from", "date_to"]:
            if self.request.GET.get(field):
                filters[field] = self.request.GET.get(field)

        return filters


# API Views
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_metrics_api(request):
    """
    API endpoint for dashboard metrics.
    """
    try:
        date_range = request.GET.get("date_range", "30d")

        analytics_service = AnalyticsService()
        metrics = analytics_service.get_dashboard_metrics(
            user=request.user, date_range=date_range
        )

        return Response({"metrics": metrics}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def referral_analytics_api(request):
    """
    API endpoint for referral analytics.
    """
    try:
        # Get filters from request
        filters = {}
        for field in [
            "status",
            "priority",
            "service_type",
            "modality",
            "date_from",
            "date_to",
        ]:
            if request.GET.get(field):
                filters[field] = request.GET.get(field)

        analytics_service = AnalyticsService()
        analytics = analytics_service.get_referral_analytics(
            user=request.user, filters=filters
        )

        return Response({"analytics": analytics}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def appointment_analytics_api(request):
    """
    API endpoint for appointment analytics.
    """
    try:
        # Get filters from request
        filters = {}
        for field in ["status", "modality", "date_from", "date_to"]:
            if request.GET.get(field):
                filters[field] = request.GET.get(field)

        analytics_service = AnalyticsService()
        analytics = analytics_service.get_appointment_analytics(
            user=request.user, filters=filters
        )

        return Response({"analytics": analytics}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def performance_metrics_api(request):
    """
    API endpoint for performance metrics.
    """
    try:
        # Get filters from request
        filters = {}
        for field in ["date_from", "date_to"]:
            if request.GET.get(field):
                filters[field] = request.GET.get(field)

        analytics_service = AnalyticsService()
        metrics = analytics_service.get_performance_metrics(
            user=request.user, filters=filters
        )

        return Response({"metrics": metrics}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_report_api(request):
    """
    API endpoint for generating reports.
    """
    try:
        report_type = request.data.get("report_type", "comprehensive")
        filters = request.data.get("filters", {})
        format = request.data.get("format", "json")

        analytics_service = AnalyticsService()
        result = analytics_service.generate_report(
            user=request.user, report_type=report_type, filters=filters, format=format
        )

        if format in ["csv", "xlsx"] and result.get("success"):
            # Return file as response
            response = HttpResponse(result["data"], content_type=result["content_type"])
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{result["filename"]}"'
            return response
        else:
            return Response(result, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)
