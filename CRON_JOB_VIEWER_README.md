# Cron Job Viewer Module

A comprehensive Django-based module for viewing, monitoring, and managing scheduled tasks (cron jobs) in your ERP system. This module integrates with Celery Beat to provide real-time monitoring and management of scheduled tasks.

## Features

### 🎯 Core Functionality
- **Real-time Monitoring**: View all scheduled tasks with their current status
- **Execution History**: Track job execution logs with detailed output
- **Schedule Management**: Support for both cron expressions and interval schedules
- **Manual Execution**: Run jobs on-demand with immediate feedback
- **Status Control**: Activate/deactivate jobs as needed

### 📊 Dashboard & Analytics
- **Statistics Overview**: Total jobs, active jobs, running jobs, failed jobs
- **Visual Charts**: Job status distribution and schedule type breakdown
- **System Health**: Database, Redis, and Celery worker status monitoring
- **Upcoming Jobs**: View jobs scheduled to run soon
- **Recent Executions**: Latest job execution results

### 🔧 Technical Features
- **Celery Integration**: Automatic logging of task executions
- **Schedule Validation**: Cron expression and interval format validation
- **Permission System**: Role-based access control for job management
- **API Endpoints**: RESTful API for programmatic access
- **Real-time Updates**: Auto-refresh functionality for live monitoring

## Architecture

### Models
- **CronJob**: Main job configuration and metadata
- **CronJobLog**: Execution history and output logging

### Components
- **Views**: Template-based frontend and REST API endpoints
- **Serializers**: Data validation and transformation
- **Celery Integration**: Automatic task monitoring and logging
- **Admin Interface**: Django admin customization for job management

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements_cron_job_viewer.txt
```

### 2. Add to Django Settings
```python
INSTALLED_APPS = [
    # ... other apps
    'cron_job_viewer',
]

# Celery Configuration (if not already configured)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### 3. Run Migrations
```bash
python manage.py makemigrations cron_job_viewer
python manage.py migrate
```

### 4. Start Services
```bash
# Start Redis (if not running)
redis-server

# Start Celery worker
celery -A logisEdge worker -l info

# Start Celery beat scheduler
celery -A logisEdge beat -l info
```

## Usage

### Accessing the Module
Navigate to: `/utilities/cron-job-viewer/`

### Dashboard
- **Overview**: Key statistics and system health
- **Charts**: Visual representation of job distribution
- **Quick Actions**: Run jobs, view logs, manage status

### Job Management
- **List View**: All jobs with filtering and search
- **Detail View**: Comprehensive job information
- **Logs View**: Execution history and output
- **Status Control**: Activate/deactivate jobs

### API Endpoints
```
GET  /api/cron-jobs/              # List all jobs
POST /api/cron-jobs/              # Create new job
GET  /api/cron-jobs/{id}/         # Get job details
PUT  /api/cron-jobs/{id}/         # Update job
DELETE /api/cron-jobs/{id}/       # Delete job
POST /api/cron-jobs/{id}/run_now/ # Execute job immediately
GET  /api/cron-jobs/statistics/   # Get job statistics
```

## Configuration

### Schedule Formats

#### Cron Expressions
Standard cron format: `minute hour day month day_of_week`
```
0 2 * * *      # Daily at 2:00 AM
0 */6 * * *    # Every 6 hours
30 9 * * 1-5   # Weekdays at 9:30 AM
```

#### Interval Schedules
Human-readable intervals: `every <number> <unit>`
```
every 5 minutes
every 1 hour
every 2 days
every 1 week
```

### Permissions
- **View Access**: Staff users and superusers
- **Management**: Job owners and superusers
- **API Access**: Authenticated users with appropriate permissions

## Celery Integration

### Automatic Logging
The module automatically logs all Celery task executions:
- Task start/completion times
- Execution duration
- Success/failure status
- Output messages and error traces

### Signal Handlers
```python
@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    # Log task start and mark job as running

@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    # Log successful completion

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    # Log failures and errors
```

### Health Monitoring
- **Worker Status**: Monitor active Celery workers
- **Queue Health**: Check task queue status
- **Performance Metrics**: Track execution times and success rates

## Customization

### Adding Custom Job Types
```python
# In your tasks.py
@shared_task(bind=True)
def custom_job(self, *args, **kwargs):
    # Your custom job logic here
    pass

# The module will automatically detect and log these tasks
```

### Custom Status Types
```python
# Extend the status choices in models.py
STATUS_CHOICES = [
    ('success', 'Success'),
    ('failed', 'Failed'),
    ('pending', 'Pending'),
    ('running', 'Running'),
    ('custom', 'Custom Status'),  # Add your custom status
]
```

### Custom Fields
```python
# Add custom fields to CronJob model
class CronJob(models.Model):
    # ... existing fields
    custom_field = models.CharField(max_length=100, blank=True)
    priority = models.IntegerField(default=1)
```

## Security Features

### Authentication & Authorization
- **User Authentication**: Login required for all views
- **Permission Checks**: Staff/admin access control
- **Owner Restrictions**: Users can only manage their own jobs

### Data Validation
- **Schedule Validation**: Prevents invalid cron expressions
- **Input Sanitization**: Protects against injection attacks
- **Size Limits**: Prevents oversized job configurations

### API Security
- **CSRF Protection**: Built-in Django CSRF protection
- **Rate Limiting**: Configurable API rate limits
- **Audit Logging**: Track all job modifications

## Monitoring & Maintenance

### Health Checks
- **Database Connectivity**: Monitor database status
- **Redis Status**: Check message broker health
- **Celery Workers**: Monitor worker availability

### Maintenance Tasks
```python
# Clean up old logs
@shared_task
def cleanup_old_cron_logs(days_to_keep=30):
    # Remove logs older than specified days

# Health check for stuck jobs
@shared_task
def health_check_cron_jobs():
    # Identify and handle stuck jobs
```

### Performance Optimization
- **Database Indexing**: Optimized queries for large datasets
- **Caching**: Redis-based caching for frequently accessed data
- **Pagination**: Efficient handling of large log collections

## Troubleshooting

### Common Issues

#### Jobs Not Running
1. Check Celery worker status
2. Verify Redis connectivity
3. Check job schedule format
4. Ensure job is active

#### Missing Logs
1. Verify Celery signal handlers are registered
2. Check database permissions
3. Monitor Celery worker logs

#### Performance Issues
1. Review database indexes
2. Check log retention settings
3. Monitor Redis memory usage

### Debug Mode
Enable debug logging in Django settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'cron_job_viewer': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Development

### Project Structure
```
cron_job_viewer/
├── models.py          # Data models
├── views.py           # View logic and API endpoints
├── serializers.py     # Data serialization
├── admin.py          # Django admin configuration
├── celery.py         # Celery integration
├── urls.py           # URL routing
├── templates/        # HTML templates
├── static/           # CSS, JavaScript, images
└── migrations/       # Database migrations
```

### Testing
```bash
# Run tests
python manage.py test cron_job_viewer

# Run with coverage
coverage run --source='.' manage.py test cron_job_viewer
coverage report
```

### Contributing
1. Follow Django coding standards
2. Add tests for new features
3. Update documentation
4. Submit pull requests

## License

This module is part of the LogisEdge ERP system and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Django and Celery documentation
3. Check system logs for error details
4. Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: August 2025  
**Compatibility**: Django 4.2+, Python 3.8+
