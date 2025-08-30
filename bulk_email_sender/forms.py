from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import (
    EmailTemplate, EmailCampaign, RecipientList, Recipient, 
    EmailSettings, EmailTracking
)


class EmailTemplateForm(forms.ModelForm):
    """Form for creating and editing email templates"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'subject', 'html_content', 'plain_text_content', 'template_type',
            'description', 'tags', 'is_active', 'sender_name', 'sender_email', 'reply_to_email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template Name'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Subject'}),
            'html_content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'HTML Email Content...',
                'id': 'html-editor'
            }),
            'plain_text_content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10, 
                'placeholder': 'Plain Text Email Content...',
                'id': 'text-editor'
            }),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'reply_to_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return []
    
    def clean_html_content(self):
        """Validate HTML content"""
        content = self.cleaned_data.get('html_content', '')
        if not content.strip():
            raise forms.ValidationError("HTML content is required")
        return content
    
    def clean_plain_text_content(self):
        """Validate plain text content"""
        content = self.cleaned_data.get('plain_text_content', '')
        if not content.strip():
            raise forms.ValidationError("Plain text content is required")
        return content


class EmailCampaignForm(forms.ModelForm):
    """Form for creating and editing email campaigns"""
    
    # Additional fields for campaign setup
    recipient_list = forms.ModelChoiceField(
        queryset=RecipientList.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select recipient list for this campaign"
    )
    
    # Campaign scheduling
    schedule_type = forms.ChoiceField(
        choices=[
            ('send_now', 'Send Now'),
            ('schedule_later', 'Schedule for Later'),
            ('draft', 'Save as Draft')
        ],
        initial='draft',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    scheduled_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    scheduled_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    class Meta:
        model = EmailCampaign
        fields = [
            'name', 'description', 'template', 'priority', 'sender_name', 'sender_email',
            'reply_to_email', 'send_speed', 'batch_size', 'tags', 'category',
            'track_opens', 'track_clicks', 'track_unsubscribes',
            'include_unsubscribe_link', 'unsubscribe_text'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campaign Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'sender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'reply_to_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'send_speed': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10000',
                'step': '1'
            }),
            'batch_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10000',
                'step': '1'
            }),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'track_opens': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'track_clicks': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'track_unsubscribes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_unsubscribe_link': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'unsubscribe_text': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for sender fields from template if available
        if self.instance and self.instance.pk and hasattr(self.instance, 'template_id') and self.instance.template_id:
            try:
                template = self.instance.template
                if template:
                    if not self.instance.sender_name:
                        self.fields['sender_name'].initial = template.sender_name
                    if not self.instance.sender_email:
                        self.fields['sender_email'].initial = template.sender_email
                    if not self.instance.reply_to_email:
                        self.fields['reply_to_email'].initial = template.reply_to_email
            except:
                # Template doesn't exist or can't be accessed, skip setting initial values
                pass
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return []
    
    def clean(self):
        """Validate campaign scheduling"""
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get('schedule_type')
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        
        if schedule_type == 'schedule_later':
            if not scheduled_date:
                raise forms.ValidationError("Scheduled date is required when scheduling for later")
            if not scheduled_time:
                raise forms.ValidationError("Scheduled time is required when scheduling for later")
            
            # Combine date and time
            scheduled_datetime = timezone.make_aware(
                timezone.datetime.combine(scheduled_date, scheduled_time)
            )
            
            if scheduled_datetime <= timezone.now():
                raise forms.ValidationError("Scheduled time must be in the future")
            
            cleaned_data['scheduled_at'] = scheduled_datetime
        
        return cleaned_data


class RecipientListForm(forms.ModelForm):
    """Form for creating and editing recipient lists"""
    
    # File upload for CSV/Excel
    file_upload = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload CSV or Excel file with recipient data"
    )
    
    # Manual entry fields
    manual_emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter email addresses, one per line or separated by commas'
        }),
        help_text="Enter email addresses manually"
    )
    
    # Database query fields
    query_model = forms.ChoiceField(
        choices=[
            ('', 'Select Model'),
            ('customer.Customer', 'Customers'),
            ('employees.Employee', 'Employees'),
            ('supplier.Supplier', 'Suppliers'),
            ('user.User', 'Users'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = RecipientList
        fields = ['name', 'description', 'list_type', 'tags', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'List Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'list_type': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return []
    
    def clean(self):
        """Validate list type specific requirements"""
        cleaned_data = super().clean()
        list_type = cleaned_data.get('list_type')
        file_upload = cleaned_data.get('file_upload')
        manual_emails = cleaned_data.get('manual_emails')
        query_model = cleaned_data.get('query_model')
        
        if list_type == 'csv_upload' and not file_upload:
            raise forms.ValidationError("File upload is required for CSV upload type")
        
        elif list_type == 'manual_entry' and not manual_emails:
            raise forms.ValidationError("Manual email entry is required for manual entry type")
        
        elif list_type == 'database_query' and not query_model:
            raise forms.ValidationError("Database model selection is required for database query type")
        
        return cleaned_data


class EmailSettingsForm(forms.ModelForm):
    """Form for configuring email provider settings"""
    
    class Meta:
        model = EmailSettings
        fields = [
            'name', 'is_active', 'provider', 'smtp_host', 'smtp_port', 'smtp_username',
            'smtp_password', 'smtp_use_tls', 'smtp_use_ssl', 'api_key', 'api_secret',
            'api_url', 'daily_limit', 'hourly_limit', 'rate_limit',
            'default_sender_name', 'default_sender_email', 'default_reply_to',
            'spf_record', 'dkim_private_key', 'dkim_selector', 'dmarc_policy'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'provider': forms.Select(attrs={'class': 'form-control'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '65535'}),
            'smtp_username': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'smtp_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'api_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
            'api_url': forms.URLInput(attrs={'class': 'form-control'}),
            'daily_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'hourly_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'rate_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'default_sender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_sender_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'default_reply_to': forms.EmailInput(attrs={'class': 'form-control'}),
            'spf_record': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dkim_private_key': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'dkim_selector': forms.TextInput(attrs={'class': 'form-control'}),
            'dmarc_policy': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """Validate provider-specific settings"""
        cleaned_data = super().clean()
        provider = cleaned_data.get('provider')
        
        if provider == 'smtp':
            if not cleaned_data.get('smtp_host'):
                raise forms.ValidationError("SMTP host is required for SMTP provider")
            if not cleaned_data.get('smtp_username'):
                raise forms.ValidationError("SMTP username is required for SMTP provider")
            if not cleaned_data.get('smtp_password'):
                raise forms.ValidationError("SMTP password is required for SMTP provider")
        
        elif provider in ['sendgrid', 'mailgun', 'amazon_ses', 'postmark']:
            if not cleaned_data.get('api_key'):
                raise forms.ValidationError(f"API key is required for {provider} provider")
            if not cleaned_data.get('api_secret'):
                raise forms.ValidationError(f"API secret is required for {provider} provider")
        
        return cleaned_data


class CampaignPreviewForm(forms.Form):
    """Form for previewing campaigns with test data"""
    
    test_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Enter test email address for preview"
    )
    
    test_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter test data as JSON (e.g., {"customer_name": "John Doe", "invoice_number": "INV-001"})'
        }),
        required=False,
        help_text="Optional: Test data for placeholders"
    )
    
    preview_type = forms.ChoiceField(
        choices=[
            ('html', 'HTML Preview'),
            ('text', 'Plain Text Preview'),
            ('both', 'Both')
        ],
        initial='both',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )


class CampaignFilterForm(forms.Form):
    """Form for filtering campaigns"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + EmailCampaign.CAMPAIGN_STATUS
    PRIORITY_CHOICES = [('', 'All Priorities')] + EmailCampaign.PRIORITY_LEVELS
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search campaigns...'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class RecipientUploadForm(forms.Form):
    """Form for uploading recipient data"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload CSV or Excel file with recipient data"
    )
    
    has_headers = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="File contains header row"
    )
    
    email_column = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email'}),
        help_text="Column name containing email addresses"
    )
    
    first_name_column = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'first_name'}),
        help_text="Column name containing first names (optional)"
    )
    
    last_name_column = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'last_name'}),
        help_text="Column name containing last names (optional)"
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 10MB")
            
            # Check file extension
            allowed_extensions = ['.csv', '.xlsx', '.xls']
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError("Only CSV and Excel files are allowed")
        
        return file
