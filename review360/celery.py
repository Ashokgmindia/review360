"""
Celery configuration for Review360.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review360.settings')

app = Celery('review360')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-session-reminders': {
        'task': 'followup.tasks.send_session_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9:00 AM
    },
    'cleanup-old-sessions': {
        'task': 'followup.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Run weekly on Monday at 2:00 AM
    },
    'sync-calendar-events': {
        'task': 'followup.tasks.sync_calendar_events',
        'schedule': crontab(minute=0, hour='*/6'),  # Run every 6 hours
    },
}

# Timezone configuration
app.conf.timezone = 'UTC'

# Task result settings
app.conf.result_expires = 3600  # Results expire after 1 hour

# Task routing
app.conf.task_routes = {
    'followup.tasks.*': {'queue': 'followup'},
    'followup.tasks.send_session_reminders': {'queue': 'reminders'},
    'followup.tasks.cleanup_old_sessions': {'queue': 'maintenance'},
    'followup.tasks.sync_calendar_events': {'queue': 'calendar'},
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
