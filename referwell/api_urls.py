"""
API URL configuration for ReferWell Direct project.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create a router for API viewsets
router = DefaultRouter()

# Register API viewsets here
# router.register(r'users', UserViewSet)
# router.register(r'referrals', ReferralViewSet)
# router.register(r'psychologists', PsychologistViewSet)
# router.register(r'matches', MatchViewSet)

urlpatterns = [
    # API router
    path('', include(router.urls)),
    
    # Authentication
    path('auth/', include('rest_framework.urls')),
    
    # App-specific API endpoints
    path('accounts/', include('accounts.api_urls')),
    path('referrals/', include('referrals.api_urls')),
    path('catalogue/', include('catalogue.api_urls')),
    path('matching/', include('matching.api_urls')),
    path('inbox/', include('inbox.api_urls')),
    path('payments/', include('payments.api_urls')),
    path('ops/', include('ops.api_urls')),
]
