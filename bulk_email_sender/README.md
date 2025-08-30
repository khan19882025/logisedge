# Bulk Email Sender - Django App

A comprehensive bulk email sending solution for Django ERP systems with advanced features for campaign management, template management, recipient management, and detailed analytics.

## Features

### 🚀 Core Functionality
- **Email Campaign Management**: Create, schedule, and manage email campaigns
- **Template Management**: HTML and plain text email templates with dynamic placeholders
- **Recipient Management**: Upload recipients via CSV/Excel or select from database
- **Bulk Sending**: Queue-based email sending with rate limiting and throttling
- **Real-time Tracking**: Monitor opens, clicks, bounces, and unsubscribes
- **Analytics Dashboard**: Comprehensive reporting and performance metrics

### 📧 Email Providers
- **SMTP**: Direct SMTP server integration
- **SendGrid**: Professional email delivery service
- **Mailgun**: Transactional email service
- **Amazon SES**: Scalable email service
- **Postmark**: Fast and reliable email delivery

### 🔒 Compliance & Security
- **SPF/DKIM/DMARC**: Email authentication and deliverability
- **Unsubscribe Management**: Automatic unsubscribe link handling
- **Bounce Management**: Hard and soft bounce handling
- **Rate Limiting**: Prevent IP/domain blacklisting
- **User Permissions**: Role-based access control

### 📊 Analytics & Reporting
- **Campaign Performance**: Open rates, click rates, delivery rates
- **Recipient Engagement**: Detailed tracking and analytics
- **Real-time Monitoring**: Live campaign progress updates
- **Export Capabilities**: Data export for external analysis

## Installation

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'bulk_email_sender',
]

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'

# Celery Configuration (for async email sending)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### 2. Run Migrations

```bash
python manage.py makemigrations bulk_email_sender
python manage.py migrate
```

### 3. Add to Main URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('bulk-email/', include('bulk_email_sender.urls')),
]
```

### 4. Install Dependencies

```bash
pip install celery redis django-celery-results
```

## Usage

### Creating Email Templates

```python
from bulk_email_sender.models import EmailTemplate

# Create a new template
template = EmailTemplate.objects.create(
    name="Welcome Email",
    subject="Welcome to {{company_name}}",
    html_content="""
    <h1>Welcome {{customer_name}}!</h1>
    <p>Thank you for joining {{company_name}}.</p>
    <p>Your account number is: {{account_number}}</p>
    """,
    plain_text_content="""
    Welcome {customer_name}!
    Thank you for joining {company_name}.
    Your account number is: {account_number}
    """,
    template_type="transactional"
)
```

### Creating Email Campaigns

```python
from bulk_email_sender.models import EmailCampaign

# Create a new campaign
campaign = EmailCampaign.objects.create(
    name="Welcome Campaign",
    template=template,
    sender_name="Company Name",
    sender_email="noreply@company.com",
    status="draft"
)

# Add recipients
from bulk_email_sender.models import Recipient
recipient = Recipient.objects.create(
    campaign=campaign,
    email="customer@example.com",
    first_name="John",
    last_name="Doe",
    custom_fields={
        "company_name": "Acme Corp",
        "customer_name": "John Doe",
        "account_number": "ACC-001"
    }
)
```

### Sending Campaigns

```python
# Start the campaign
campaign.status = "queued"
campaign.save()

# The campaign will be processed automatically via Celery
```

## Models

### EmailTemplate
- **name**: Template name
- **subject**: Email subject line
- **html_content**: HTML email content
- **plain_text_content**: Plain text email content
- **template_type**: Type of template (newsletter, promotional, etc.)
- **available_placeholders**: Dynamic variables available in template

### EmailCampaign
- **name**: Campaign name
- **template**: Associated email template
- **status**: Campaign status (draft, scheduled, queued, sending, completed)
- **sender_name**: Campaign sender name
- **sender_email**: Campaign sender email
- **scheduled_at**: When to start sending
- **send_speed**: Emails per minute
- **batch_size**: Emails per batch

### RecipientList
- **name**: List name
- **list_type**: Source type (CSV upload, database query, manual entry)
- **source_file**: Uploaded file for CSV/Excel imports
- **query_model**: Django model for database queries
- **query_filters**: Filters for database queries

### Recipient
- **campaign**: Associated email campaign
- **email**: Recipient email address
- **first_name**: Recipient first name
- **last_name**: Recipient last name
- **status**: Email status (pending, sent, delivered, opened, clicked)
- **custom_fields**: Dynamic data for template placeholders

### EmailTracking
- **recipient**: Associated recipient
- **tracking_type**: Event type (open, click, bounce, unsubscribe)
- **timestamp**: When the event occurred
- **ip_address**: IP address of the event
- **user_agent**: User agent string
- **metadata**: Additional tracking data

### EmailQueue
- **campaign**: Associated campaign
- **batch_number**: Batch sequence number
- **status**: Queue status (pending, processing, completed, failed)
- **total_emails**: Total emails in batch
- **sent_emails**: Successfully sent emails
- **failed_emails**: Failed emails

### EmailSettings
- **name**: Configuration name
- **provider**: Email service provider
- **smtp_host**: SMTP server host
- **smtp_port**: SMTP server port
- **api_key**: API key for service providers
- **daily_limit**: Daily sending limit
- **rate_limit**: Emails per minute

## Views

### Dashboard
- **URL**: `/bulk-email/`
- **View**: `dashboard`
- **Description**: Main dashboard with campaign statistics and quick actions

### Templates
- **List**: `/bulk-email/templates/`
- **Create**: `/bulk-email/templates/create/`
- **Detail**: `/bulk-email/templates/<id>/`
- **Edit**: `/bulk-email/templates/<id>/edit/`
- **Delete**: `/bulk-email/templates/<id>/delete/`

### Campaigns
- **List**: `/bulk-email/campaigns/`
- **Create**: `/bulk-email/campaigns/create/`
- **Detail**: `/bulk-email/campaigns/<id>/`
- **Edit**: `/bulk-email/campaigns/<id>/edit/`
- **Preview**: `/bulk-email/campaigns/<id>/preview/`
- **Start**: `/bulk-email/campaigns/<id>/start/`
- **Pause**: `/bulk-email/campaigns/<id>/pause/`
- **Cancel**: `/bulk-email/campaigns/<id>/cancel/`

### Recipient Lists
- **List**: `/bulk-email/recipient-lists/`
- **Create**: `/bulk-email/recipient-lists/create/`
- **Detail**: `/bulk-email/recipient-lists/<id>/`

### Recipients
- **Upload**: `/bulk-email/recipients/upload/`
- **Upload Confirm**: `/bulk-email/recipients/upload/confirm/`

### Settings
- **List**: `/bulk-email/settings/`
- **Create**: `/bulk-email/settings/create/`
- **Detail**: `/bulk-email/settings/<id>/`

### Tracking
- **Dashboard**: `/bulk-email/tracking/`
- **Webhook**: `/bulk-email/webhook/tracking/`

## Forms

### EmailTemplateForm
- Template creation and editing
- HTML and plain text content
- Placeholder management
- Sender information

### EmailCampaignForm
- Campaign configuration
- Scheduling options
- Sending parameters
- Tracking settings

### RecipientListForm
- List creation
- File upload handling
- Database query configuration
- Manual entry

### EmailSettingsForm
- Provider configuration
- SMTP settings
- API credentials
- Sending limits

## Admin Interface

The app provides a comprehensive Django admin interface with:

- **List Views**: Sortable and filterable lists
- **Detail Views**: Comprehensive object details
- **Inline Editing**: Edit related objects
- **Bulk Actions**: Perform actions on multiple objects
- **Search**: Full-text search across models
- **Filters**: Advanced filtering options

## Celery Tasks

### Email Sending Tasks
- `create_campaign_queue`: Create email batches
- `process_email_queue`: Process email batches
- `send_single_email`: Send individual emails
- `start_campaign_sending`: Start campaign sending process

### File Processing Tasks
- `process_recipient_list_file`: Process uploaded CSV/Excel files
- `validate_recipient_data`: Validate recipient information
- `import_recipients`: Import recipients to campaigns

### Maintenance Tasks
- `cleanup_old_tracking`: Clean up old tracking data
- `generate_campaign_reports`: Generate campaign reports
- `test_email_configuration`: Test email provider settings

## Configuration

### Environment Variables
```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys (for service providers)
SENDGRID_API_KEY=your-sendgrid-key
MAILGUN_API_KEY=your-mailgun-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### Django Settings
```python
# Bulk Email Sender Settings
BULK_EMAIL_SENDER = {
    'DEFAULT_PROVIDER': 'smtp',
    'MAX_DAILY_EMAILS': 10000,
    'MAX_HOURLY_EMAILS': 1000,
    'DEFAULT_BATCH_SIZE': 1000,
    'DEFAULT_SEND_SPEED': 100,
    'ENABLE_TRACKING': True,
    'TRACKING_PIXEL': True,
    'LINK_TRACKING': True,
    'BOUNCE_HANDLING': True,
    'UNSUBSCRIBE_HANDLING': True,
}
```

## Security Considerations

### Email Authentication
- Configure SPF, DKIM, and DMARC records
- Use dedicated sending domains
- Implement proper authentication

### Rate Limiting
- Respect provider limits
- Implement gradual sending
- Monitor delivery rates

### Data Protection
- Encrypt sensitive data
- Implement access controls
- Regular security audits

## Performance Optimization

### Database Optimization
- Use database indexes
- Implement query optimization
- Regular database maintenance

### Caching Strategy
- Cache frequently accessed data
- Use Redis for session storage
- Implement CDN for static files

### Email Delivery
- Use connection pooling
- Implement retry logic
- Monitor delivery performance

## Monitoring & Logging

### System Monitoring
- Monitor queue performance
- Track email delivery rates
- Monitor system resources

### Error Handling
- Comprehensive error logging
- Alert notifications
- Automatic retry mechanisms

### Performance Metrics
- Response times
- Throughput rates
- Error rates

## Troubleshooting

### Common Issues

#### Emails Not Sending
- Check email provider configuration
- Verify SMTP credentials
- Check firewall settings
- Review rate limits

#### Low Delivery Rates
- Check SPF/DKIM configuration
- Monitor bounce rates
- Review sender reputation
- Check content quality

#### Performance Issues
- Monitor queue processing
- Check database performance
- Review server resources
- Optimize queries

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
        'bulk_email_sender': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Testing
```bash
# Run tests
python manage.py test bulk_email_sender

# Run with coverage
coverage run --source='.' manage.py test bulk_email_sender
coverage report
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## Changelog

### Version 1.0.0
- Initial release
- Basic email campaign functionality
- Template management
- Recipient management
- Basic tracking

### Version 1.1.0 (Planned)
- Advanced analytics
- A/B testing
- Advanced segmentation
- API endpoints

## Roadmap

### Short Term
- Enhanced reporting
- Email preview functionality
- Advanced filtering
- Bulk operations

### Medium Term
- Marketing automation
- Advanced segmentation
- Personalization engine
- Integration APIs

### Long Term
- AI-powered optimization
- Predictive analytics
- Advanced automation
- Multi-channel support
