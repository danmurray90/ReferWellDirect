"""
Views for matching app.
"""
import json
import time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from referrals.models import Referral

from .models import CalibrationModel, MatchingAlgorithm, MatchingRun, MatchingThreshold
from .routing_service import ReferralRoutingService
from .services import MatchingService


def api_auth_required(view_func):
    """
    Decorator to require authentication for API endpoints.
    Returns 403 for unauthenticated requests instead of redirecting.
    """

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper


class MatchingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Matching dashboard view.
    """

    template_name = "matching/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get routing statistics
        routing_service = ReferralRoutingService()
        routing_stats = routing_service.get_routing_statistics()

        # Get referral queues
        status_filter = self.request.GET.get("status")
        priority_filter = self.request.GET.get("priority")
        service_type_filter = self.request.GET.get("service_type")

        # Build filter query
        filter_q = Q()
        if status_filter:
            filter_q &= Q(status=status_filter)
        if priority_filter:
            filter_q &= Q(priority=priority_filter)
        if service_type_filter:
            filter_q &= Q(service_type=service_type_filter)

        # Get referrals by status
        high_touch_referrals = (
            Referral.objects.filter(status=Referral.Status.HIGH_TOUCH_QUEUE)
            .filter(filter_q)
            .order_by("-created_at")[:20]
        )

        auto_routed_referrals = (
            Referral.objects.filter(status=Referral.Status.SHORTLISTED)
            .filter(filter_q)
            .order_by("-created_at")[:20]
        )

        manual_review_referrals = (
            Referral.objects.filter(status=Referral.Status.MATCHING)
            .filter(filter_q)
            .order_by("-created_at")[:20]
        )

        context.update(
            {
                "total_referrals": routing_stats["total_referrals"],
                "auto_routed": routing_stats["auto_routed"],
                "high_touch_queue": routing_stats["high_touch_routed"],
                "manual_review": routing_stats["manual_review"],
                "high_touch_referrals": high_touch_referrals,
                "auto_routed_referrals": auto_routed_referrals,
                "manual_review_referrals": manual_review_referrals,
                "recent_runs": MatchingRun.objects.all().order_by("-created_at")[:10],
                "algorithms": MatchingAlgorithm.objects.filter(is_active=True),
                "calibration_models": CalibrationModel.objects.filter(is_active=True),
            }
        )
        return context


class AlgorithmListView(LoginRequiredMixin, TemplateView):
    """
    Algorithm list view.
    """

    template_name = "matching/algorithm_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["algorithms"] = MatchingAlgorithm.objects.all().order_by("-created_at")
        return context


class CalibrationView(LoginRequiredMixin, TemplateView):
    """
    Calibration view.
    """

    template_name = "matching/calibration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["calibration_models"] = CalibrationModel.objects.all().order_by(
            "-created_at"
        )
        context["thresholds"] = MatchingThreshold.objects.filter(is_active=True)
        return context


class MatchingResultsView(LoginRequiredMixin, TemplateView):
    """
    Matching results view.
    """

    template_name = "matching/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral_id = kwargs.get("referral_id")

        if referral_id:
            referral = get_object_or_404(Referral, id=referral_id)

            # Run matching
            start_time = time.time()
            matching_service = MatchingService()
            matches, routing_decision = matching_service.find_matches(
                referral, limit=10
            )
            processing_time = time.time() - start_time

            # Categorize matches by confidence level
            high_confidence_matches = [m for m in matches if m["score"] >= 0.7]

            # Determine confidence level for display
            highest_score = max([m["score"] for m in matches]) if matches else 0
            if highest_score >= 0.7:
                confidence_level = "high"
            elif highest_score >= 0.5:
                confidence_level = "medium"
            else:
                confidence_level = "low"

            # Add card class for styling
            for match in matches:
                if match["score"] >= 0.8:
                    match["card_class"] = "top"
                elif match["score"] >= 0.6:
                    match["card_class"] = "good"
                else:
                    match["card_class"] = "fair"

            context.update(
                {
                    "referral": referral,
                    "matches": matches,
                    "routing_decision": routing_decision,
                    "highest_score": highest_score,
                    "confidence_level": confidence_level,
                    "high_confidence_matches": high_confidence_matches,
                    "processing_time": processing_time,
                    "algorithm_version": "1.0",  # This would come from the matching service
                }
            )

        return context


class PerformanceMetricsView(LoginRequiredMixin, TemplateView):
    """
    Performance metrics view.
    """

    template_name = "matching/performance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get cache statistics
        try:
            cache_keys = cache.keys("*") or []
            cache_stats = {
                "total_keys": len(cache_keys),
                "embedding_keys": len(
                    [k for k in cache_keys if k.startswith("embedding_")]
                ),
                "bm25_keys": len([k for k in cache_keys if k.startswith("bm25_")]),
                "threshold_keys": len(
                    [k for k in cache_keys if k.startswith("threshold_config_")]
                ),
            }
        except Exception:
            cache_stats = {
                "total_keys": 0,
                "embedding_keys": 0,
                "bm25_keys": 0,
                "threshold_keys": 0,
            }

        # Get matching statistics
        matching_runs = MatchingRun.objects.all()
        total_referrals = (
            matching_runs.aggregate(total=Count("total_referrals"))["total"] or 0
        )
        successful_matches = (
            matching_runs.aggregate(successful=Count("successful_matches"))[
                "successful"
            ]
            or 0
        )

        matching_stats = {
            "total_referrals": total_referrals,
            "successful_matches": successful_matches,
            "success_rate": (successful_matches / total_referrals * 100)
            if total_referrals > 0
            else 0,
            "avg_processing_time": matching_runs.aggregate(
                avg=Count("processing_time_seconds")
            )["avg"]
            or 0,
        }

        # Get system health (simplified)
        system_health = {
            "cache_status": "good" if cache_stats["total_keys"] > 0 else "warning",
            "database_status": "good",  # This would check actual DB connectivity
            "vector_service_status": "good",  # This would check vector service
            "uptime": "24h 15m",  # This would be calculated from system start time
        }

        # Get threshold configurations
        thresholds = MatchingThreshold.objects.filter(is_active=True)

        context.update(
            {
                "cache_stats": cache_stats,
                "matching_stats": matching_stats,
                "system_health": system_health,
                "thresholds": thresholds,
            }
        )

        return context


# API Views
@require_http_methods(["POST"])
@api_auth_required
def find_matches_api(request):
    """
    API endpoint to find matches for a referral.
    """
    try:
        data = json.loads(request.body)
        referral_id = data.get("referral_id")

        if not referral_id:
            return JsonResponse({"error": "referral_id is required"}, status=400)

        referral = get_object_or_404(Referral, id=referral_id)

        # Run matching
        start_time = time.time()
        matching_service = MatchingService()
        matches, routing_decision = matching_service.find_matches(referral, limit=10)
        processing_time = time.time() - start_time

        # Convert matches to serializable format
        serializable_matches = []
        for match in matches:
            serializable_matches.append(
                {
                    "psychologist_id": str(match["psychologist"].id),
                    "psychologist_name": match["psychologist"].user.get_full_name(),
                    "score": match["score"],
                    "explanation": match["explanation"],
                }
            )

        return JsonResponse(
            {
                "matches": serializable_matches,
                "routing_decision": routing_decision,
                "processing_time": processing_time,
                "total_matches": len(serializable_matches),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@api_auth_required
def routing_statistics_api(request):
    """
    API endpoint to get routing statistics.
    """
    try:
        routing_service = ReferralRoutingService()
        stats = routing_service.get_routing_statistics()
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@api_auth_required
def high_touch_queue_api(request):
    """
    API endpoint to get high-touch queue referrals.
    """
    try:
        routing_service = ReferralRoutingService()
        referrals = routing_service.get_high_touch_queue(limit=50)

        serializable_referrals = []
        for referral in referrals:
            serializable_referrals.append(
                {
                    "id": str(referral.id),
                    "referral_id": referral.referral_id,
                    "presenting_problem": referral.presenting_problem,
                    "patient_name": referral.patient.get_full_name(),
                    "referrer_name": referral.referrer.get_full_name(),
                    "priority": referral.priority,
                    "created_at": referral.created_at.isoformat(),
                }
            )

        return JsonResponse({"referrals": serializable_referrals})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@api_auth_required
def clear_cache_api(request):
    """
    API endpoint to clear all caches.
    """
    try:
        # Set a test cache key first for testing
        cache.set("test_key", "test_value", 300)

        routing_service = ReferralRoutingService()
        routing_service.clear_all_caches()

        # Clear Django cache as well
        cache.clear()

        return JsonResponse(
            {"success": True, "message": "All caches cleared successfully"}
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
@api_auth_required
def threshold_config_api(request):
    """
    API endpoint to get threshold configurations.
    """
    try:
        thresholds = MatchingThreshold.objects.filter(is_active=True)
        serializable_thresholds = []
        for threshold in thresholds:
            serializable_thresholds.append(
                {
                    "user_type": threshold.user_type,
                    "user_type_display": threshold.get_user_type_display(),
                    "auto_threshold": threshold.auto_threshold,
                    "high_touch_threshold": threshold.high_touch_threshold,
                }
            )

        return JsonResponse({"thresholds": serializable_thresholds})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@api_auth_required
def update_threshold_api(request):
    """
    API endpoint to update threshold configuration.
    """
    try:
        data = json.loads(request.body)
        user_type = data.get("user_type")
        auto_threshold = data.get("auto_threshold")
        high_touch_threshold = data.get("high_touch_threshold")

        if not all(
            [user_type, auto_threshold is not None, high_touch_threshold is not None]
        ):
            return JsonResponse(
                {
                    "error": "user_type, auto_threshold, and high_touch_threshold are required"
                },
                status=400,
            )

        if auto_threshold < high_touch_threshold:
            return JsonResponse(
                {"error": "auto_threshold must be >= high_touch_threshold"}, status=400
            )

        threshold, created = MatchingThreshold.objects.get_or_create(
            user_type=user_type,
            defaults={
                "auto_threshold": auto_threshold,
                "high_touch_threshold": high_touch_threshold,
            },
        )

        if not created:
            threshold.auto_threshold = auto_threshold
            threshold.high_touch_threshold = high_touch_threshold
            threshold.save()

        # Invalidate cache
        routing_service = ReferralRoutingService()
        routing_service.invalidate_threshold_cache(user_type)

        return JsonResponse(
            {"success": True, "message": "Threshold updated successfully"}
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@api_auth_required
def performance_metrics_api(request):
    """
    API endpoint to get performance metrics.
    """
    try:
        # This would return the same data as the PerformanceMetricsView
        # but in JSON format for AJAX calls
        view = PerformanceMetricsView()
        view.request = request
        context = view.get_context_data()

        return JsonResponse(
            {
                "cache_stats": context["cache_stats"],
                "matching_stats": context["matching_stats"],
                "system_health": context["system_health"],
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
