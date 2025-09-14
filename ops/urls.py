"""
URL configuration for ops app.
"""
from django.urls import path
from . import views

app_name = 'ops'

urlpatterns = [
    # Web views
    path('', views.OpsDashboardView.as_view(), name='dashboard'),
    path('audit/', views.AuditEventListView.as_view(), name='audit_list'),
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    path('logs/', views.SystemLogListView.as_view(), name='system_log_list'),
]
