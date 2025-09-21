"""
Analytics URL configuration for referrals app.
"""
from django.urls import path
from . import analytics_views

app_name = 'referrals_analytics'

urlpatterns = [
    # Analytics views
    path('', analytics_views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('referrals/', analytics_views.ReferralAnalyticsView.as_view(), name='referral_analytics'),
    path('appointments/', analytics_views.AppointmentAnalyticsView.as_view(), name='appointment_analytics'),
    path('performance/', analytics_views.PerformanceMetricsView.as_view(), name='performance_metrics'),
    
    # Analytics API endpoints
    path('api/dashboard-metrics/', analytics_views.dashboard_metrics_api, name='dashboard_metrics_api'),
    path('api/referral-analytics/', analytics_views.referral_analytics_api, name='referral_analytics_api'),
    path('api/appointment-analytics/', analytics_views.appointment_analytics_api, name='appointment_analytics_api'),
    path('api/performance-metrics/', analytics_views.performance_metrics_api, name='performance_metrics_api'),
    path('api/generate-report/', analytics_views.generate_report_api, name='generate_report_api'),
]
