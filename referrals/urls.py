"""
URL configuration for referrals app.
"""
from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    # Web views
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('create/', views.CreateReferralView.as_view(), name='create'),
    path('list/', views.ReferralListView.as_view(), name='list'),
    path('<uuid:pk>/', views.ReferralDetailView.as_view(), name='referral_detail'),
    path('<uuid:referral_id>/shortlist/', views.ShortlistView.as_view(), name='shortlist'),
]
