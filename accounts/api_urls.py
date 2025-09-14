"""
API URL configuration for accounts app.
"""
from django.urls import path
from . import views

app_name = 'accounts_api'

urlpatterns = [
    # User API endpoints
    path('users/', views.UserListAPIView.as_view(), name='user-list'),
    path('users/<uuid:id>/', views.UserDetailAPIView.as_view(), name='user-detail'),
    
    # Organisation API endpoints
    path('organisations/', views.OrganisationListAPIView.as_view(), name='organisation-list'),
    path('organisations/<uuid:id>/', views.OrganisationDetailAPIView.as_view(), name='organisation-detail'),
    
    # User-Organisation relationship endpoints
    path('assign-user-to-organisation/', views.assign_user_to_organisation, name='assign-user-to-organisation'),
]
