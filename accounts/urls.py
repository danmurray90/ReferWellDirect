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

urlpatterns = [
    # Web views
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API views
    path('api/', include(router.urls)),
]
