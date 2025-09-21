"""
URL configuration for referrals app.
"""
from django.urls import path, include
from . import views

app_name = 'referrals'

urlpatterns = [
    # Web views
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('create/', views.CreateReferralView.as_view(), name='create'),
    path('list/', views.ReferralListView.as_view(), name='list'),
    path('<uuid:pk>/', views.ReferralDetailView.as_view(), name='referral_detail'),
    path('<uuid:pk>/edit/', views.EditReferralView.as_view(), name='edit'),
    path('<uuid:referral_id>/shortlist/', views.ShortlistView.as_view(), name='shortlist'),
    
    # Analytics
    path('analytics/', include('referrals.analytics_urls')),
    
    # API
    path('api/', include('referrals.api_urls')),
]
