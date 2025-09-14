"""
URL configuration for matching app.
"""
from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    # Web views
    path('', views.MatchingDashboardView.as_view(), name='dashboard'),
    path('algorithms/', views.AlgorithmListView.as_view(), name='algorithm_list'),
    path('calibration/', views.CalibrationView.as_view(), name='calibration'),
    path('results/<uuid:referral_id>/', views.MatchingResultsView.as_view(), name='results'),
    path('performance/', views.PerformanceMetricsView.as_view(), name='performance_metrics'),
    
    # API endpoints
    path('api/find-matches/', views.find_matches_api, name='find_matches'),
    path('api/routing-statistics/', views.routing_statistics_api, name='routing_statistics'),
    path('api/high-touch-queue/', views.high_touch_queue_api, name='high_touch_queue'),
    path('api/clear-cache/', views.clear_cache_api, name='clear_cache'),
    path('api/threshold-config/', views.threshold_config_api, name='threshold_config'),
    path('api/update-threshold/', views.update_threshold_api, name='update_threshold'),
    path('api/performance-metrics/', views.performance_metrics_api, name='performance_metrics'),
]
