# Email Configuration & Testing App

A comprehensive Django application for managing and testing email server configurations in ERP systems. This app provides a user-friendly interface to configure, test, and monitor SMTP, IMAP, and POP3 email services.

## Features

### 🔧 Email Configuration Management
- **Multiple Protocol Support**: SMTP, IMAP, and POP3 configurations
- **Flexible Encryption**: None, SSL, TLS, and STARTTLS support
- **Authentication Options**: Username/password authentication with security
- **Connection Settings**: Timeout and concurrent connection management
- **Default Configurations**: Set primary configurations per protocol

### 🧪 Comprehensive Testing
- **Connection Testing**: Verify server connectivity
- **Authentication Testing**: Validate login credentials
- **Send Test Emails**: Test outgoing email functionality
- **Receive Testing**: Verify incoming email capabilities
- **Full Configuration Tests**: End-to-end configuration validation

### 📊 Monitoring & Analytics
- **Real-time Dashboard**: Live configuration health monitoring
- **Test Results History**: Track all test outcomes and performance
- **Status Tracking**: Monitor configuration health over time
- **Performance Metrics**: Connection times and success rates

### 📧 Email Notifications
- **System Alerts**: Automated notifications for configuration issues
- **Business Workflows**: Support for automated business processes
- **Scheduled Sending**: Time-based email delivery
- **Retry Mechanisms**: Automatic retry for failed notifications

## Installation

### 1. Add to INSTALLED_APPS
```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'email_configuration',
]
```

### 2. Include URLs
```python
# urls.py
urlpatterns = [
    # ... other URLs
    path('utilities/email-configuration/', include('email_configuration.urls', namespace='email_configuration')),
]
```

### 3. Run Migrations
```bash
python manage.py makemigrations email_configuration
python manage.py migrate email_configuration
```

### 4. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

## Usage

### Accessing the App
Navigate to `/utilities/email-configuration/` in your browser to access the main dashboard.

### Creating Email Configurations

#### SMTP Configuration Example
```python
# Example SMTP settings for Gmail
name: "Gmail SMTP"
protocol: "smtp"
host: "smtp.gmail.com"
port: 587
encryption: "tls"
username: "your-email@gmail.com"
password: "your-app-password"
use_authentication: True
timeout: 30
max_connections: 10
```

#### IMAP Configuration Example
```python
# Example IMAP settings for Gmail
name: "Gmail IMAP"
protocol: "imap"
host: "imap.gmail.com"
port: 993
encryption: "ssl"
username: "your-email@gmail.com"
password: "your-app-password"
use_authentication: True
fetch_interval: 5
delete_after_fetch: False
```

#### POP3 Configuration Example
```python
# Example POP3 settings for Gmail
name: "Gmail POP3"
protocol: "pop3"
host: "pop.gmail.com"
port: 995
encryption: "ssl"
username: "your-email@gmail.com"
password: "your-app-password"
use_authentication: True
fetch_interval: 10
delete_after_fetch: True
```

### Testing Configurations

1. **Navigate to Configuration List**: View all email configurations
2. **Click Test Button**: Use the test button for any configuration
3. **Select Test Type**: Choose from available test options
4. **Review Results**: Check test outcomes and error details

### Available Test Types

- **Connection Test**: Basic server connectivity
- **Authentication Test**: Login credential validation
- **Send Test Email**: Outgoing email functionality
- **Receive Test Email**: Incoming email capabilities
- **Full Configuration Test**: Complete end-to-end validation

## Models

### EmailConfiguration
Core model for storing email server configurations:
- Basic information (name, protocol, host, port)
- Security settings (encryption, authentication)
- Connection parameters (timeout, max connections)
- Status tracking (active, default, test results)

### EmailTestResult
Stores results of configuration tests:
- Test type and status
- Performance metrics (duration, timestamps)
- Error details and stack traces
- Test parameters used

### EmailNotification
Manages email notifications and alerts:
- Notification types and priorities
- Recipient management (to, cc, bcc)
- Scheduling and delivery status
- Retry mechanisms and error handling

## API Endpoints

### Configuration Management
- `GET /configurations/` - List all configurations
- `POST /configurations/create/` - Create new configuration
- `GET /configurations/{id}/` - View configuration details
- `PUT /configurations/{id}/edit/` - Update configuration
- `DELETE /configurations/{id}/delete/` - Delete configuration

### Testing
- `POST /configurations/{id}/test/` - Test configuration
- `GET /test-results/` - View test results history

### Notifications
- `GET /notifications/` - List notifications
- `POST /notifications/create/` - Create notification

### Health Monitoring
- `GET /api/health/` - Configuration health status
- `GET /api/statistics/` - Performance statistics

## Security Features

- **Password Protection**: Secure password storage and handling
- **Authentication Required**: Login required for all operations
- **Permission System**: Role-based access control
- **Input Validation**: Comprehensive form validation
- **CSRF Protection**: Built-in Django security

## Customization

### Adding New Protocols
Extend the `PROTOCOL_CHOICES` in models.py:
```python
PROTOCOL_CHOICES = [
    ('smtp', 'SMTP'),
    ('imap', 'IMAP'),
    ('pop3', 'POP3'),
    ('exchange', 'Microsoft Exchange'),  # New protocol
]
```

### Custom Test Types
Add new test types in the `EmailTestForm`:
```python
TEST_TYPE_CHOICES = [
    # ... existing choices
    ('custom_test', 'Custom Test Type'),
]
```

### Notification Templates
Customize email notification templates in the templates directory.

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check firewall settings
   - Verify port accessibility
   - Increase timeout values

2. **Authentication Failures**
   - Verify username/password
   - Check for 2FA requirements
   - Ensure app passwords are used for Gmail

3. **SSL/TLS Issues**
   - Verify certificate validity
   - Check encryption method compatibility
   - Test with different encryption options

### Debug Mode
Enable Django debug mode to see detailed error messages and stack traces.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation
- Review the troubleshooting section
- Open an issue on GitHub
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Basic email configuration management
- Testing functionality
- Dashboard and monitoring
- Admin interface integration
