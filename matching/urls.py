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
]
