"""
URL configuration for inbox app.
"""
from django.urls import path
from . import views

app_name = 'inbox'

urlpatterns = [
    # Web views
    path('', views.InboxView.as_view(), name='inbox'),
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
]
