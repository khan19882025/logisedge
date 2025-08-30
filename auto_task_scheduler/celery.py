import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logisEdge.settings')

app = Celery('auto_task_scheduler')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery Beat Schedule Configuration
app.conf.beat_schedule = {
    # Sync database schedules every 5 minutes
    'sync-database-schedules': {
        'task': 'auto_task_scheduler.tasks.sync_celery_schedules',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Clean up old logs daily at 2 AM
    'cleanup-old-logs': {
        'task': 'auto_task_scheduler.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Health check every hour
    'health-check': {
        'task': 'auto_task_scheduler.tasks.system_health_check',
        'schedule': 3600.0,  # 1 hour
    },
}

# Task routing
app.conf.task_routes = {
    'auto_task_scheduler.tasks.*': {'queue': 'scheduler'},
    'auto_task_scheduler.tasks.execute_backup_task': {'queue': 'backup'},
    'auto_task_scheduler.tasks.execute_report_task': {'queue': 'reports'},
    'auto_task_scheduler.tasks.execute_email_task': {'queue': 'email'},
    'auto_task_scheduler.tasks.execute_sync_task': {'queue': 'sync'},
}

# Task serialization
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Result backend
app.conf.result_backend = 'redis://localhost:6379/1'

# Worker configuration
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_max_tasks_per_child = 1000

# Task time limits
app.conf.task_soft_time_limit = 300  # 5 minutes
app.conf.task_time_limit = 600       # 10 minutes

# Retry configuration
app.conf.task_default_retry_delay = 300
app.conf.task_max_retries = 3

# Logging
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')


# Import crontab for schedule configuration
try:
    from celery.schedules import crontab
except ImportError:
    # Fallback if crontab is not available
    def crontab(**kwargs):
        """Fallback crontab function"""
        return kwargs
