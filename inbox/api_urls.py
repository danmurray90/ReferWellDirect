"""
API URL patterns for inbox app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, NotificationTemplateViewSet, NotificationPreferenceViewSet,
    NotificationChannelViewSet, notification_list, notification_detail,
    mark_notification_read, notification_stats
)

app_name = 'inbox_api'

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'notification-channels', NotificationChannelViewSet, basename='notification-channel')

urlpatterns = [
    path('', include(router.urls)),
    # Legacy API endpoints for backward compatibility
    path('notifications/legacy/', notification_list, name='notification-list-legacy'),
    path('notifications/legacy/<uuid:notification_id>/', notification_detail, name='notification-detail-legacy'),
    path('notifications/legacy/<uuid:notification_id>/mark-read/', mark_notification_read, name='notification-mark-read-legacy'),
    path('notifications/legacy/stats/', notification_stats, name='notification-stats-legacy'),
]
