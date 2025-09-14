"""
URL configuration for accounts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'accounts'

# Create router for API views
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'organisations', views.OrganisationViewSet)
router.register(r'onboarding-steps', views.OnboardingStepViewSet)
router.register(r'onboarding-progress', views.UserOnboardingProgressViewSet)
router.register(r'onboarding-sessions', views.OnboardingSessionViewSet)

urlpatterns = [
    # Web views
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Onboarding views
    path('onboarding/start/', views.onboarding_start, name='onboarding_start'),
    path('onboarding/step/<uuid:step_id>/', views.onboarding_step, name='onboarding_step'),
    path('onboarding/step/<uuid:step_id>/complete/', views.onboarding_complete_step, name='onboarding_complete_step'),
    path('onboarding/step/<uuid:step_id>/skip/', views.onboarding_skip_step, name='onboarding_skip_step'),
    path('onboarding/progress/', views.onboarding_progress, name='onboarding_progress'),
    
    # API views
    path('api/', include(router.urls)),
]
