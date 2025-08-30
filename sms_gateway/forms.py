from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone
from .models import SMSGateway, SMSTestResult, SMSMessage


class SMSGatewayForm(forms.ModelForm):
    """Form for creating and editing SMS Gateway configurations"""
    
    # Custom validation for phone number format
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    # Override fields with custom widgets and validation
    api_secret = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="API secret or password (will be encrypted)"
    )
    
    sender_id = forms.CharField(
        validators=[phone_regex],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Sender ID or from number (e.g., +971501234567)"
    )
    
    timeout = forms.IntegerField(
        min_value=5,
        max_value=300,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Request timeout in seconds (5-300)"
    )
    
    max_retries = forms.IntegerField(
        min_value=0,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Maximum retry attempts (0-10)"
    )
    
    rate_limit_per_second = forms.IntegerField(
        min_value=1,
        max_value=1000,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Messages per second limit (1-1000)"
    )
    
    rate_limit_per_minute = forms.IntegerField(
        min_value=1,
        max_value=60000,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Messages per minute limit (1-60000)"
    )
    
    rate_limit_per_hour = forms.IntegerField(
        min_value=1,
        max_value=3600000,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Messages per hour limit (1-3600000)"
    )
    
    class Meta:
        model = SMSGateway
        fields = [
            'name', 'gateway_type', 'is_active',
            'api_key', 'api_secret', 'username', 'sender_id',
            'api_url', 'http_method', 'timeout', 'max_retries', 'encryption',
            'default_encoding', 'max_message_length', 'support_unicode',
            'rate_limit_per_second', 'rate_limit_per_minute', 'rate_limit_per_hour'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gateway_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'api_url': forms.URLInput(attrs={'class': 'form-control'}),
            'http_method': forms.Select(attrs={'class': 'form-control'}),
            'encryption': forms.Select(attrs={'class': 'form-control'}),
            'default_encoding': forms.TextInput(attrs={'class': 'form-control'}),
            'max_message_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'support_unicode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for new gateways
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['support_unicode'].initial = True
    
    def clean(self):
        """Custom validation for the form"""
        cleaned_data = super().clean()
        
        # Validate rate limits are consistent
        per_second = cleaned_data.get('rate_limit_per_second', 0)
        per_minute = cleaned_data.get('rate_limit_per_minute', 0)
        per_hour = cleaned_data.get('rate_limit_per_hour', 0)
        
        if per_second * 60 > per_minute:
            raise forms.ValidationError(
                "Rate limit per minute should be at least 60 times the per-second limit."
            )
        
        if per_minute * 60 > per_hour:
            raise forms.ValidationError(
                "Rate limit per hour should be at least 60 times the per-minute limit."
            )
        
        # Validate API URL format
        api_url = cleaned_data.get('api_url')
        if api_url and not api_url.startswith(('http://', 'https://')):
            raise forms.ValidationError("API URL must start with http:// or https://")
        
        return cleaned_data


class SMSTestForm(forms.ModelForm):
    """Form for running SMS tests"""
    
    # Test configuration
    test_type = forms.ChoiceField(
        choices=SMSTestResult.TEST_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Type of test to perform"
    )
    
    recipient_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+971501234567'}),
        help_text="Test recipient phone number"
    )
    
    test_message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter test message content...'}),
        help_text="Test message content"
    )
    
    message_encoding = forms.ChoiceField(
        choices=[
            ('UTF-8', 'UTF-8 (Standard)'),
            ('UTF-16', 'UTF-16 (Unicode)'),
            ('GSM-7', 'GSM-7 (Standard SMS)'),
            ('UCS-2', 'UCS-2 (Extended)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Message encoding for the test"
    )
    
    test_environment = forms.ChoiceField(
        choices=[
            ('production', 'Production'),
            ('staging', 'Staging'),
            ('development', 'Development'),
            ('testing', 'Testing'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Test environment"
    )
    
    # Advanced options
    include_unicode_test = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include Unicode character testing"
    )
    
    include_rate_limit_test = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include rate limiting tests"
    )
    
    class Meta:
        model = SMSTestResult
        fields = ['test_type', 'recipient_number', 'test_message', 'message_encoding', 'test_environment']
    
    def __init__(self, *args, **kwargs):
        self.gateway = kwargs.pop('gateway', None)
        super().__init__(*args, **kwargs)
        
        if self.gateway:
            # Pre-fill gateway-specific defaults
            self.fields['message_encoding'].initial = self.gateway.default_encoding
            self.fields['test_message'].initial = f"Test message from {self.gateway.name} - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
    
    def clean_recipient_number(self):
        """Validate phone number format"""
        phone_regex = RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )
        phone_number = self.cleaned_data['recipient_number']
        phone_regex(phone_number)
        return phone_number
    
    def clean_test_message(self):
        """Validate test message content"""
        message = self.cleaned_data['test_message']
        if not message.strip():
            raise forms.ValidationError("Test message cannot be empty")
        
        # Check message length against gateway limits
        if self.gateway and len(message) > self.gateway.max_message_length:
            raise forms.ValidationError(
                f"Message length ({len(message)}) exceeds gateway limit ({self.gateway.max_message_length})"
            )
        
        return message


class SMSMessageForm(forms.ModelForm):
    """Form for sending SMS messages"""
    
    # Message content
    recipient_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+971501234567'}),
        help_text="Recipient phone number"
    )
    
    message_content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your message...'}),
        help_text="SMS message content"
    )
    
    # Message settings
    priority = forms.ChoiceField(
        choices=SMSMessage.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Message priority level"
    )
    
    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        ),
        help_text="Schedule message for later (optional)"
    )
    
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        ),
        help_text="Message expiration time (optional)"
    )
    
    # Categorization
    category = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Message category (e.g., OTP, Alert, Notification)"
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3'}),
        help_text="Comma-separated tags for categorization"
    )
    
    class Meta:
        model = SMSMessage
        fields = [
            'recipient_number', 'message_content', 'priority',
            'scheduled_at', 'expires_at', 'category', 'tags'
        ]
    
    def __init__(self, *args, **kwargs):
        self.gateway = kwargs.pop('gateway', None)
        super().__init__(*args, **kwargs)
        
        if self.gateway:
            # Pre-fill gateway-specific defaults
            self.fields['message_content'].initial = f"Message from {self.gateway.name}"
    
    def clean_recipient_number(self):
        """Validate phone number format"""
        phone_regex = RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )
        phone_number = self.cleaned_data['recipient_number']
        phone_regex(phone_number)
        return phone_number
    
    def clean_message_content(self):
        """Validate message content"""
        message = self.cleaned_data['message_content']
        if not message.strip():
            raise forms.ValidationError("Message content cannot be empty")
        
        # Check message length against gateway limits
        if self.gateway and len(message) > self.gateway.max_message_length:
            raise forms.ValidationError(
                f"Message length ({len(message)}) exceeds gateway limit ({self.gateway.max_message_length})"
            )
        
        return message
    
    def clean_scheduled_at(self):
        """Validate scheduled time is in the future"""
        scheduled_at = self.cleaned_data.get('scheduled_at')
        if scheduled_at and scheduled_at <= timezone.now():
            raise forms.ValidationError("Scheduled time must be in the future")
        return scheduled_at
    
    def clean_expires_at(self):
        """Validate expiration time is after scheduled time"""
        scheduled_at = self.cleaned_data.get('scheduled_at')
        expires_at = self.cleaned_data.get('expires_at')
        
        if scheduled_at and expires_at and expires_at <= scheduled_at:
            raise forms.ValidationError("Expiration time must be after scheduled time")
        
        return expires_at
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Split by comma and clean up
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        return []


class SMSGatewayTestForm(forms.Form):
    """Form for comprehensive gateway testing"""
    
    # Test selection
    test_connection = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Test API connection and endpoint accessibility"
    )
    
    test_authentication = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Test API credentials and authentication"
    )
    
    test_message_send = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send a test message to verify delivery"
    )
    
    test_unicode = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Test Unicode character support"
    )
    
    test_rate_limits = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Test rate limiting behavior"
    )
    
    # Test parameters
    test_recipient = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+971501234567'}),
        help_text="Test recipient phone number (required for message tests)"
    )
    
    test_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Test message content...'}),
        help_text="Test message content (optional)"
    )
    
    unicode_test_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'مرحبا بالعالم! 🌍 Hello World! 你好世界！'}),
        help_text="Unicode test message with Arabic, emojis, and other characters"
    )
    
    # Advanced options
    test_environment = forms.ChoiceField(
        choices=[
            ('production', 'Production'),
            ('staging', 'Staging'),
            ('development', 'Development'),
        ],
        initial='production',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Test environment"
    )
    
    include_performance_metrics = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include performance metrics in test results"
    )
    
    def clean(self):
        """Custom validation for test form"""
        cleaned_data = super().clean()
        
        # Validate that at least one test is selected
        tests_selected = any([
            cleaned_data.get('test_connection'),
            cleaned_data.get('test_authentication'),
            cleaned_data.get('test_message_send'),
            cleaned_data.get('test_unicode'),
            cleaned_data.get('test_rate_limits'),
        ])
        
        if not tests_selected:
            raise forms.ValidationError("Please select at least one test to run")
        
        # Validate recipient number is provided for message tests
        if (cleaned_data.get('test_message_send') or cleaned_data.get('test_unicode')) and not cleaned_data.get('test_recipient'):
            raise forms.ValidationError("Recipient number is required for message tests")
        
        return cleaned_data
