"""
Celery configuration for ReferWell Direct project.
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'referwell.settings.development')

app = Celery('referwell')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule
app.conf.beat_schedule = {
    'refresh-embeddings': {
        'task': 'matching.tasks.refresh_embeddings',
        'schedule': 3600.0,  # Every hour
    },
    'run-calibration': {
        'task': 'matching.tasks.run_calibration',
        'schedule': 86400.0,  # Daily
    },
    'cleanup-expired-invites': {
        'task': 'referrals.tasks.cleanup_expired_invites',
        'schedule': 3600.0,  # Every hour
    },
    'send-notification-reminders': {
        'task': 'inbox.tasks.send_notification_reminders',
        'schedule': 1800.0,  # Every 30 minutes
    },
}

# Celery timezone
app.conf.timezone = 'Europe/London'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
