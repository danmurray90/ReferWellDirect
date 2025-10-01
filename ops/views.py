"""
Views for ops app.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from .models import AuditEvent, Metric, SystemLog


class OpsDashboardView(LoginRequiredMixin, TemplateView):
    """
    Operations dashboard view.
    """

    template_name = "ops/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get recent audit events
        context["recent_audit_events"] = AuditEvent.objects.all().order_by(
            "-created_at"
        )[:10]

        # Get key metrics
        context["key_metrics"] = Metric.objects.filter(
            name__in=["total_referrals", "active_users", "matching_success_rate"]
        ).order_by("name")

        # Get recent system logs
        context["recent_logs"] = SystemLog.objects.filter(
            level__in=["ERROR", "CRITICAL"]
        ).order_by("-created_at")[:10]

        return context


class AuditEventListView(LoginRequiredMixin, ListView):
    """
    Audit event list view.
    """

    model = AuditEvent
    template_name = "ops/audit_list.html"
    context_object_name = "audit_events"
    paginate_by = 50

    def get_queryset(self):
        return AuditEvent.objects.all().order_by("-created_at")


class MetricsView(LoginRequiredMixin, TemplateView):
    """
    Metrics view.
    """

    template_name = "ops/metrics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["metrics"] = Metric.objects.all().order_by("name")
        return context


class SystemLogListView(LoginRequiredMixin, ListView):
    """
    System log list view.
    """

    model = SystemLog
    template_name = "ops/system_log_list.html"
    context_object_name = "system_logs"
    paginate_by = 100

    def get_queryset(self):
        return SystemLog.objects.all().order_by("-created_at")
