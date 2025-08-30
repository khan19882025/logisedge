# System Error & Debug Logs Module

A comprehensive Django application for monitoring, analyzing, and managing system errors, warnings, and debug events with advanced features for troubleshooting, root cause analysis, and compliance.

## Features

### 🚨 **Comprehensive Error Logging**
- **Multi-level Severity**: DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL
- **Detailed Context**: Module, function, line number, file path, stack traces
- **User Tracking**: User actions, IP addresses, user agents, request data
- **Performance Metrics**: Execution time, memory usage, CPU usage
- **Object Relationships**: Generic foreign keys to any Django model

### 🔍 **Advanced Search & Filtering**
- **Date Range Filtering**: Customizable time periods
- **Multi-criteria Search**: Log type, severity, status, module, function
- **Performance Filters**: Execution time thresholds, memory usage
- **Security Filters**: Security levels, categories, impact assessment
- **Tag-based Filtering**: Custom tags for categorization

### 📊 **Real-time Analytics & Dashboards**
- **Interactive Charts**: Log type distribution, severity trends, daily activity
- **Performance Metrics**: Average execution times, error patterns
- **Module Analysis**: Error counts by module, critical issue tracking
- **User Activity**: User-specific error patterns and statistics

### 🎯 **Error Pattern Recognition**
- **Automatic Detection**: Identifies recurring error patterns
- **Pattern Analysis**: Occurrence counts, severity trends, affected users
- **Resolution Tracking**: Pattern resolution status and notes
- **Impact Assessment**: Performance impact analysis

### 🐛 **Debug Session Management**
- **Session Tracking**: Development, testing, debugging sessions
- **Context Preservation**: Environment, version, tags, related logs
- **Duration Monitoring**: Session timing and log counts
- **Collaborative Debugging**: Multiple users can contribute to sessions

### 📋 **Bulk Operations & Automation**
- **Mass Actions**: Resolve, ignore, escalate, archive multiple logs
- **Tag Management**: Add/remove tags in bulk
- **User Assignment**: Assign logs to specific users for resolution
- **Automated Workflows**: Streamlined error resolution processes

### 📤 **Multi-format Export**
- **Export Formats**: CSV, JSON, XML, PDF, Excel
- **Customizable Fields**: Select specific fields for export
- **Metadata Inclusion**: Optional stack traces and context data
- **Filtered Exports**: Export based on current search criteria

### 🔒 **Log Retention & Compliance**
- **Retention Policies**: Time-based, size-based, severity-based policies
- **Automated Cleanup**: Archive, compress, or delete old logs
- **Compliance Support**: Audit trail preservation and reporting
- **Storage Optimization**: Efficient log storage and retrieval

### 🛡️ **Security & Audit Features**
- **Security Event Logging**: Authentication, authorization, data access
- **Audit Trails**: Complete model change tracking
- **User Activity Monitoring**: Login/logout, action tracking
- **Compliance Reporting**: Regulatory compliance support

## Installation

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'system_logs',
]

# Optional: Configure logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'system_logs': {
            'level': 'INFO',
            'class': 'system_logs.handlers.SystemLogHandler',
        },
    },
    'loggers': {
        'system_logs': {
            'handlers': ['system_logs'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. Run Migrations

```bash
python manage.py makemigrations system_logs
python manage.py migrate
```

### 3. Add to Main URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('utilities/system-logs/', include('system_logs.urls', namespace='system_logs')),
]
```

### 4. Include in Navigation

```html
<!-- base.html or navigation template -->
<li class="nav-item">
    <a class="nav-link" href="{% url 'system_logs:dashboard' %}">
        <i class="fas fa-exclamation-triangle"></i>
        System Errors & Debug Logs
    </a>
</li>
```

## Usage

### Basic Logging

```python
from system_logs.signals import log_system_event

# Log a simple error
log_system_event(
    log_type='EXCEPTION',
    severity='ERROR',
    error_message='Database connection failed',
    error_type='DatabaseError',
    module='database',
    function='connect',
    user=request.user,
    request=request
)

# Log performance metrics
log_system_event(
    log_type='PERFORMANCE',
    severity='WARNING',
    error_message='Slow database query detected',
    error_type='PERFORMANCE_ISSUE',
    module='database',
    function='execute_query',
    execution_time=5.2,
    user=request.user
)
```

### Using the Decorator

```python
from system_logs.signals import log_action

@log_action('USER_REGISTRATION', 'User registration completed', 'INFO')
def register_user(request, form):
    # User registration logic
    user = form.save()
    return user
```

### Security Event Logging

```python
from system_logs.signals import log_security_event

# Log security events
log_security_event(
    event_type='LOGIN_ATTEMPT',
    description='Failed login attempt detected',
    severity='WARNING',
    user=user,
    request=request,
    security_details={
        'ip_address': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'attempt_count': 3
    }
)
```

### Performance Monitoring

```python
from system_logs.signals import log_performance_metric
import time

def expensive_operation():
    start_time = time.time()
    
    # ... operation logic ...
    
    execution_time = time.time() - start_time
    log_performance_metric(
        module='data_processing',
        function='expensive_operation',
        execution_time=execution_time,
        tags=['performance', 'data_processing']
    )
```

## Models

### SystemLog
Main model for storing all system events and errors.

**Key Fields:**
- `timestamp`: When the event occurred
- `log_type`: Type of log (EXCEPTION, WARNING, DEBUG, etc.)
- `severity`: Severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL)
- `error_message`: Human-readable error description
- `stack_trace`: Full stack trace for exceptions
- `module`/`function`: Code location information
- `user`: Associated user (if applicable)
- `execution_time`: Performance metrics
- `tags`: Custom categorization tags

### ErrorPattern
Tracks recurring error patterns for analysis.

**Key Features:**
- Automatic pattern detection
- Occurrence counting and statistics
- Resolution tracking
- Impact analysis

### DebugSession
Manages debugging sessions and their associated logs.

**Key Features:**
- Session lifecycle management
- Context preservation
- Duration tracking
- Collaborative debugging

### LogRetentionPolicy
Defines automated log retention and cleanup policies.

**Policy Types:**
- Time-based retention
- Size-based retention
- Severity-based retention
- Pattern-based retention

## Views

### Dashboard (`dashboard`)
Comprehensive overview with charts, statistics, and quick actions.

### List Views
- **SystemLogListView**: Paginated list with advanced filtering
- **ErrorPatternListView**: Error pattern analysis
- **DebugSessionListView**: Active debugging sessions

### Detail Views
- **SystemLogDetailView**: Complete log information
- **ErrorPatternDetailView**: Pattern analysis and resolution
- **DebugSessionDetailView**: Session details and logs

### Search & Export
- **system_log_search**: Advanced search interface
- **system_log_export**: Multi-format data export
- **system_log_chart_data**: AJAX endpoint for chart data

### Bulk Operations
- **bulk_action**: Mass operations on multiple logs
- **log_retention_cleanup**: Automated log cleanup

## Forms

### SystemLogSearchForm
Advanced search and filtering with multiple criteria.

### SystemLogExportForm
Export configuration with field selection and format options.

### BulkActionForm
Mass operations with confirmation and additional parameters.

### ErrorPatternForm
Pattern creation and resolution management.

### DebugSessionForm
Session configuration and management.

## Admin Interface

The Django admin interface provides comprehensive management capabilities:

- **SystemLog**: Full log management with bulk actions
- **ErrorPattern**: Pattern analysis and resolution
- **DebugSession**: Session lifecycle management
- **LogRetentionPolicy**: Policy configuration and execution
- **LogExport**: Export history and management

## API Endpoints

### Chart Data
```
GET /utilities/system-logs/chart-data/?days=30
```

### Bulk Actions
```
POST /utilities/system-logs/bulk-action/
```

### Export
```
POST /utilities/system-logs/export/
```

## Configuration

### Environment Variables

```bash
# Log retention settings
SYSTEM_LOGS_RETENTION_DAYS=90
SYSTEM_LOGS_MAX_SIZE_MB=1000

# Performance thresholds
SYSTEM_LOGS_SLOW_QUERY_THRESHOLD=1.0
SYSTEM_LOGS_CRITICAL_THRESHOLD=10.0

# Export settings
SYSTEM_LOGS_EXPORT_MAX_RECORDS=10000
SYSTEM_LOGS_EXPORT_TIMEOUT=300
```

### Custom Settings

```python
# settings.py
SYSTEM_LOGS = {
    'ENABLE_AUTO_CLEANUP': True,
    'CLEANUP_INTERVAL_HOURS': 24,
    'MAX_LOG_AGE_DAYS': 365,
    'ENABLE_REAL_TIME_UPDATES': False,
    'CHART_UPDATE_INTERVAL': 30,
    'DEFAULT_EXPORT_FORMAT': 'CSV',
    'ENABLE_PATTERN_DETECTION': True,
    'PATTERN_SIMILARITY_THRESHOLD': 0.8,
}
```

## Security Considerations

### Permission System
- All views require authentication
- Granular permissions for different operations
- User-specific log access controls

### Data Privacy
- Sensitive data filtering in exports
- User consent for detailed logging
- GDPR compliance features

### Audit Trail
- Complete action logging
- User responsibility tracking
- Change history preservation

## Performance Optimization

### Database Indexing
- Optimized indexes for common queries
- Partitioning for large log volumes
- Efficient pagination

### Caching
- Chart data caching
- Search result caching
- Pattern analysis caching

### Background Processing
- Asynchronous log processing
- Batch operations for bulk actions
- Scheduled cleanup tasks

## Monitoring & Alerting

### Real-time Monitoring
- Live dashboard updates
- WebSocket support for real-time data
- Performance threshold alerts

### Alert Configuration
- Configurable alert thresholds
- Multiple notification channels
- Escalation procedures

### Health Checks
- System status monitoring
- Performance metrics tracking
- Error rate monitoring

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check log retention policies
   - Optimize database queries
   - Enable log compression

2. **Slow Performance**
   - Review database indexes
   - Optimize chart queries
   - Enable caching

3. **Export Failures**
   - Check file permissions
   - Verify export format support
   - Monitor timeout settings

### Debug Mode

```python
# Enable debug logging
SYSTEM_LOGS_DEBUG = True

# Verbose logging
LOGGING['loggers']['system_logs']['level'] = 'DEBUG'
```

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Run tests
python manage.py test system_logs

# Run linting
flake8 system_logs/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Comprehensive docstrings
- Unit test coverage

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

## Changelog

### Version 1.0.0
- Initial release
- Core logging functionality
- Dashboard and analytics
- Export capabilities
- Admin interface

### Future Versions
- Real-time WebSocket updates
- Advanced pattern recognition
- Machine learning integration
- Mobile app support
- API rate limiting
