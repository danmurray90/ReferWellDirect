"""
Server-Sent Events (SSE) views for real-time notifications.
"""
import json
import time
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django.conf import settings
from .services import NotificationService


class NotificationSSEView(View):
    """
    Server-Sent Events view for real-time notifications.
    """
    
    @method_decorator(login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        """Stream notifications via SSE."""
        
        def event_stream():
            """Generate SSE event stream."""
            user_id = request.user.id
            last_notification_id = request.GET.get('last_id', 0)
            
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': time.time()})}\n\n"
            
            # Keep connection alive and check for new notifications
            while True:
                try:
                    # Check for new notifications
                    cache_key = f"notifications_stream_{user_id}"
                    new_notifications = cache.get(cache_key, [])
                    
                    # Filter notifications newer than last_id
                    if last_notification_id:
                        new_notifications = [
                            n for n in new_notifications 
                            if n.get('id', 0) > int(last_notification_id)
                        ]
                    
                    # Send new notifications
                    for notification in new_notifications:
                        yield f"data: {json.dumps(notification)}\n\n"
                        last_notification_id = notification.get('id', last_notification_id)
                    
                    # Send heartbeat every 30 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                    
                    # Sleep for 1 second before next check
                    time.sleep(1)
                    
                except Exception as e:
                    # Send error event
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    break
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        
        # Set SSE headers
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        return response


@login_required
@require_http_methods(["GET"])
def notification_sse(request):
    """
    Simple SSE endpoint for notifications.
    """
    def event_stream():
        """Generate SSE event stream."""
        user_id = request.user.id
        service = NotificationService()
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"
        
        # Keep connection alive
        while True:
            try:
                # Get latest notifications
                notifications = service.get_user_notifications(
                    user=request.user,
                    unread_only=True,
                    limit=10
                )
                
                # Send notification count
                yield f"data: {json.dumps({'type': 'notification_count', 'count': len(notifications)})}\n\n"
                
                # Sleep for 5 seconds before next check
                time.sleep(5)
                
            except Exception as e:
                # Send error event
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    
    # Set SSE headers
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    
    return response


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def notification_sse_test(request):
    """
    Test endpoint to trigger SSE notifications.
    """
    try:
        service = NotificationService()
        
        # Create a test notification
        notification = service.create_notification(
            user=request.user,
            notification_type='system',
            title='SSE Test Notification',
            message='This is a test notification sent via Server-Sent Events.',
            priority='medium'
        )
        
        # Add to cache for SSE stream
        user_id = request.user.id
        cache_key = f"notifications_stream_{user_id}"
        notifications = cache.get(cache_key, [])
        
        notification_data = {
            'id': notification.id,
            'type': 'notification',
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'priority': notification.priority,
            'is_important': notification.is_important,
            'created_at': notification.created_at.isoformat(),
        }
        
        notifications.append(notification_data)
        cache.set(cache_key, notifications, 300)  # Cache for 5 minutes
        
        return JsonResponse({
            'success': True,
            'message': 'Test notification sent via SSE',
            'notification_id': str(notification.id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
