"""
Views for inbox app.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Notification, NotificationTemplate


class InboxView(LoginRequiredMixin, TemplateView):
    """
    Main inbox view.
    """
    template_name = 'inbox/inbox.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get unread notifications
        context['unread_notifications'] = Notification.objects.filter(
            user=user, is_read=False
        ).order_by('-created_at')[:10]
        
        # Get recent notifications
        context['recent_notifications'] = Notification.objects.filter(
            user=user
        ).order_by('-created_at')[:20]
        
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    """
    List view for notifications.
    """
    model = Notification
    template_name = 'inbox/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a specific notification.
    """
    model = Notification
    template_name = 'inbox/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark notification as read when viewed
        notification = self.get_object()
        notification.mark_as_read()
        return response
