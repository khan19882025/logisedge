# Auto Task Scheduler - LogisEdge ERP

A comprehensive automated task scheduling system for ERP operations, built with Django, Celery, and Redis.

## 🚀 Features

### Core Functionality
- **Flexible Scheduling**: Daily, weekly, monthly, and one-time task scheduling
- **Multiple Task Types**: Database backup, report generation, email notifications, data sync, and custom tasks
- **Real-time Monitoring**: Live dashboard with task status and execution logs
- **Automatic Retries**: Configurable retry logic for failed tasks
- **User Management**: Role-based access control and task ownership

### Task Types Supported
- **Database Backup**: Automated database backups with cleanup
- **Report Generation**: Sales, inventory, financial, and custom reports
- **Email Notifications**: Automated email sending with templates
- **Data Synchronization**: Sync data between different systems
- **Custom Tasks**: Execute any Python function with parameters

### Advanced Features
- **Dynamic Scheduling**: Database-driven schedules with Celery Beat integration
- **Execution Logging**: Comprehensive logging of all task executions
- **Health Monitoring**: System health checks and status monitoring
- **Performance Metrics**: Task execution time and success rate tracking
- **Mobile Responsive**: Modern UI that works on all devices

## 🏗️ Architecture

### Backend Stack
- **Django 4.2+**: Web framework and ORM
- **Django REST Framework**: API endpoints and serialization
- **Celery 5.2+**: Asynchronous task execution
- **Redis**: Message broker and result backend
- **PostgreSQL/MySQL**: Database storage

### Frontend Stack
- **Vanilla JavaScript**: Modern ES6+ with async/await
- **Chart.js**: Data visualization and charts
- **Responsive CSS**: Mobile-first design with CSS Grid and Flexbox
- **Font Awesome**: Icon library for UI elements

## 📁 Project Structure

```
auto_task_scheduler/
├── models.py              # Database models
├── serializers.py         # API serializers
├── views.py              # API views and template views
├── tasks.py              # Celery task definitions
├── celery.py             # Celery configuration
├── urls.py               # URL routing
├── admin.py              # Django admin configuration
├── templates/            # HTML templates
│   └── auto_task_scheduler/
│       ├── dashboard.html
│       ├── create_task.html
│       ├── task_list.html
│       ├── task_detail.html
│       └── task_logs.html
├── static/               # Static files
│   ├── css/
│   │   └── task_scheduler.css
│   └── js/
│       ├── task_scheduler.js
│       └── components/
└── migrations/           # Database migrations
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Redis server
- PostgreSQL or MySQL database
- Virtual environment (recommended)

### 1. Install Dependencies
```bash
pip install -r requirements_auto_task_scheduler.txt
```

### 2. Configure Django Settings
Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'auto_task_scheduler',
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Celery Beat Schedule
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. Run Migrations
```bash
python manage.py makemigrations auto_task_scheduler
python manage.py migrate
```

### 4. Start Services
```bash
# Start Redis (in separate terminal)
redis-server

# Start Celery worker (in separate terminal)
celery -A auto_task_scheduler worker --loglevel=info

# Start Celery beat (in separate terminal)
celery -A auto_task_scheduler beat --loglevel=info

# Start Django development server
python manage.py runserver
```

## 🔧 Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Task Configuration
Tasks can be configured through the Django admin interface or via API:

```python
# Example task configuration
task = ScheduledTask.objects.create(
    name="Daily Sales Report",
    task_type="report",
    schedule_type="daily",
    schedule_time=time(9, 0),  # 9:00 AM
    task_function="auto_task_scheduler.tasks.execute_report_task",
    task_parameters={
        "report_type": "sales",
        "format": "pdf",
        "email_recipients": ["manager@company.com"]
    },
    max_execution_time=600,  # 10 minutes
    retry_on_failure=True,
    max_retries=3
)
```

## 📊 API Endpoints

### Task Management
- `GET /api/scheduled-tasks/` - List all tasks
- `POST /api/scheduled-tasks/` - Create new task
- `GET /api/scheduled-tasks/{id}/` - Get task details
- `PUT /api/scheduled-tasks/{id}/` - Update task
- `DELETE /api/scheduled-tasks/{id}/` - Delete task

### Task Operations
- `POST /api/scheduled-tasks/{id}/run/` - Run task manually
- `POST /api/scheduled-tasks/{id}/activate/` - Activate task
- `POST /api/scheduled-tasks/{id}/deactivate/` - Deactivate task
- `POST /api/scheduled-tasks/{id}/pause/` - Pause task

### Monitoring
- `GET /api/scheduled-tasks/statistics/` - Get task statistics
- `GET /api/scheduled-tasks/{id}/logs/` - Get task execution logs
- `GET /api/task-logs/recent/` - Get recent executions
- `GET /api/health-check/` - System health status

## 🎯 Usage Examples

### Creating a Daily Backup Task
```python
from auto_task_scheduler.models import ScheduledTask
from datetime import time

# Create daily database backup at 2:00 AM
backup_task = ScheduledTask.objects.create(
    name="Daily Database Backup",
    description="Automated daily backup of the main database",
    task_type="backup",
    schedule_type="daily",
    schedule_time=time(2, 0),
    task_function="auto_task_scheduler.tasks.execute_backup_task",
    task_parameters={
        "backup_dir": "/backups/daily/",
        "max_backups": 7
    },
    max_execution_time=1800,  # 30 minutes
    retry_on_failure=True,
    max_retries=2
)

# Activate the task
backup_task.activate()
```

### Creating a Weekly Report Task
```python
# Create weekly sales report every Monday at 8:00 AM
report_task = ScheduledTask.objects.create(
    name="Weekly Sales Report",
    description="Generate and email weekly sales report",
    task_type="report",
    schedule_type="weekly",
    schedule_time=time(8, 0),
    monday=True,  # Only run on Mondays
    task_function="auto_task_scheduler.tasks.execute_report_task",
    task_parameters={
        "report_type": "sales",
        "format": "pdf",
        "email_recipients": ["sales@company.com", "management@company.com"]
    }
)

report_task.activate()
```

### Custom Task Function
```python
# In your custom module
def custom_inventory_check():
    """Custom inventory checking logic"""
    from inventory.models import Product
    
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('reorder_level')
    )
    
    if low_stock_products.exists():
        # Send notification
        send_low_stock_alert(low_stock_products)
    
    return f"Checked {low_stock_products.count()} low stock products"

# Create scheduled task for custom function
custom_task = ScheduledTask.objects.create(
    name="Inventory Stock Check",
    task_type="custom",
    schedule_type="daily",
    schedule_time=time(6, 0),  # 6:00 AM
    task_function="your_app.tasks.custom_inventory_check",
    task_parameters={}
)
```

## 📈 Dashboard Features

### Statistics Cards
- Total scheduled tasks
- Active tasks count
- Paused tasks count
- Failed executions (24h)

### Task Management
- View upcoming tasks
- Recent execution logs
- Quick action buttons
- System health status

### Charts and Visualizations
- Task distribution by type
- Execution success rates
- Performance metrics

## 🔒 Security Features

### Authentication & Authorization
- User authentication required for all operations
- Role-based permissions (can_manage_tasks, can_run_tasks)
- Task ownership and visibility controls
- Public/private task settings

### Input Validation
- Comprehensive form validation
- SQL injection prevention
- XSS protection
- File upload security

### API Security
- CSRF protection
- Rate limiting support
- Input sanitization
- Secure task execution

## 🚨 Monitoring & Alerts

### Health Checks
- Database connectivity
- Celery worker status
- Redis connection
- Task execution monitoring

### Logging
- Detailed execution logs
- Error tracking and reporting
- Performance metrics
- Audit trail

### Alerts
- Failed task notifications
- System health alerts
- Performance warnings
- Custom alert rules

## 🚀 Production Deployment

### Recommended Setup
```bash
# Install production dependencies
pip install gunicorn supervisor

# Configure supervisor for Celery
sudo nano /etc/supervisor/conf.d/celery.conf

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery_worker
sudo supervisorctl start celery_beat
```

### Performance Optimization
- Use Redis cluster for high availability
- Implement task result caching
- Configure worker concurrency
- Monitor memory usage

### Scaling Considerations
- Multiple Celery workers
- Redis cluster setup
- Database connection pooling
- Load balancing

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest-django factory-boy coverage

# Run tests
pytest auto_task_scheduler/

# Generate coverage report
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Coverage
- Model validation and methods
- API endpoints and serializers
- Task execution logic
- Admin interface
- Frontend functionality

## 🐛 Troubleshooting

### Common Issues

#### Celery Worker Not Starting
```bash
# Check Redis connection
redis-cli ping

# Verify Celery configuration
celery -A auto_task_scheduler inspect active
```

#### Tasks Not Executing
```bash
# Check Celery Beat schedule
celery -A auto_task_scheduler beat --loglevel=info

# Verify task registration
celery -A auto_task_scheduler inspect registered
```

#### Database Connection Issues
```bash
# Test database connection
python manage.py dbshell

# Check migration status
python manage.py showmigrations
```

### Debug Mode
```python
# Enable debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'auto_task_scheduler': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📚 API Documentation

### Authentication
All API endpoints require authentication. Include the CSRF token in requests:

```javascript
// Get CSRF token
const csrfToken = document.querySelector('[name=csrf-token]').getAttribute('content');

// Make authenticated request
fetch('/api/scheduled-tasks/', {
    headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json',
    }
});
```

### Request/Response Examples

#### Create Task
```json
POST /api/scheduled-tasks/
{
    "name": "Daily Backup",
    "task_type": "backup",
    "schedule_type": "daily",
    "schedule_time": "02:00:00",
    "task_function": "auto_task_scheduler.tasks.execute_backup_task",
    "task_parameters": {
        "backup_dir": "/backups/",
        "max_backups": 7
    }
}
```

#### Task Response
```json
{
    "id": "uuid-here",
    "name": "Daily Backup",
    "status": "active",
    "next_run_at": "2024-01-15T02:00:00Z",
    "created_at": "2024-01-14T10:00:00Z"
}
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
- Check the troubleshooting section
- Review the API documentation
- Search existing issues
- Create a new issue with detailed information

### Contact Information
- Project maintainer: [Your Name]
- Email: [your.email@example.com]
- GitHub: [your-github-username]

---

**Note**: This module is designed for production use in enterprise environments. Always test thoroughly in a staging environment before deploying to production.
