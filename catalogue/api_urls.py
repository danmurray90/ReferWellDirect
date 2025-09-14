"""
API URL configuration for catalogue app.
"""
from django.urls import path
from . import views

app_name = 'catalogue_api'

urlpatterns = [
    # Psychologist API endpoints
    path('psychologists/', views.PsychologistListAPIView.as_view(), name='psychologist-list'),
    path('psychologists/<uuid:id>/', views.PsychologistDetailAPIView.as_view(), name='psychologist-detail'),
    path('psychologists/<uuid:psychologist_id>/availability/', views.update_psychologist_availability, name='update-availability'),
    path('psychologists/<uuid:psychologist_id>/availability-slots/', views.add_availability_slot, name='add-availability-slot'),
    
    # Availability API endpoints
    path('psychologists/<uuid:psychologist_id>/availabilities/', views.AvailabilityListAPIView.as_view(), name='availability-list'),
    
    # Specialism API endpoints
    path('specialisms/', views.SpecialismListAPIView.as_view(), name='specialism-list'),
    
    # Qualification API endpoints
    path('qualifications/', views.QualificationListAPIView.as_view(), name='qualification-list'),
    
    # Review API endpoints
    path('psychologists/<uuid:psychologist_id>/reviews/', views.ReviewListAPIView.as_view(), name='review-list'),
]
