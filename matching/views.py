"""
Views for matching app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import MatchingRun, MatchingAlgorithm, CalibrationModel, MatchingThreshold


class MatchingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Matching dashboard view.
    """
    template_name = 'matching/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_runs'] = MatchingRun.objects.all().order_by('-created_at')[:10]
        context['algorithms'] = MatchingAlgorithm.objects.filter(is_active=True)
        context['calibration_models'] = CalibrationModel.objects.filter(is_active=True)
        return context


class AlgorithmListView(LoginRequiredMixin, TemplateView):
    """
    Algorithm list view.
    """
    template_name = 'matching/algorithm_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['algorithms'] = MatchingAlgorithm.objects.all().order_by('-created_at')
        return context


class CalibrationView(LoginRequiredMixin, TemplateView):
    """
    Calibration view.
    """
    template_name = 'matching/calibration.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['calibration_models'] = CalibrationModel.objects.all().order_by('-created_at')
        context['thresholds'] = MatchingThreshold.objects.filter(is_active=True)
        return context
