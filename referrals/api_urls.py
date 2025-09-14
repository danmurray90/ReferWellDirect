"""
API URL configuration for referrals app.
"""
from django.urls import path
from . import views

app_name = 'referrals_api'

urlpatterns = [
    # Referral API endpoints
    path('referrals/', views.ReferralListAPIView.as_view(), name='referral-list'),
    path('referrals/<uuid:id>/', views.ReferralDetailAPIView.as_view(), name='referral-detail'),
    path('referrals/<uuid:referral_id>/submit/', views.submit_referral, name='submit-referral'),
    
    # Candidate API endpoints
    path('referrals/<uuid:referral_id>/candidates/', views.CandidateListAPIView.as_view(), name='candidate-list'),
    path('candidates/<uuid:id>/', views.CandidateDetailAPIView.as_view(), name='candidate-detail'),
    path('candidates/<uuid:candidate_id>/respond/', views.respond_to_invitation, name='respond-to-invitation'),
]
