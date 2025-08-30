from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import EmailConfiguration, EmailTestResult, EmailNotification


class EmailConfigurationForm(forms.ModelForm):
    """Form for creating and editing email configurations"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Leave blank to keep current password"
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Confirm the password"
    )
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'name', 'protocol', 'host', 'port', 'encryption',
            'username', 'password', 'use_authentication',
            'timeout', 'max_connections', 'delete_after_fetch',
            'fetch_interval', 'is_active', 'is_default'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'protocol': forms.Select(attrs={'class': 'form-control'}),
            'host': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control'}),
            'encryption': forms.Select(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'use_authentication': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'timeout': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_connections': forms.NumberInput(attrs={'class': 'form-control'}),
            'delete_after_fetch': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fetch_interval': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        # Validate port numbers
        port = cleaned_data.get('port')
        if port:
            if port < 1 or port > 65535:
                raise forms.ValidationError("Port must be between 1 and 65535.")
        
        # Validate timeout
        timeout = cleaned_data.get('timeout')
        if timeout and timeout < 1:
            raise forms.ValidationError("Timeout must be at least 1 second.")
        
        # Validate fetch interval
        fetch_interval = cleaned_data.get('fetch_interval')
        if fetch_interval and fetch_interval < 1:
            raise forms.ValidationError("Fetch interval must be at least 1 minute.")
        
        return cleaned_data


class EmailTestForm(forms.Form):
    """Form for testing email configurations"""
    
    TEST_TYPE_CHOICES = [
        ('connection', 'Connection Test'),
        ('authentication', 'Authentication Test'),
        ('send_test', 'Send Test Email'),
        ('receive_test', 'Receive Test Email'),
        ('full_test', 'Full Configuration Test'),
    ]
    
    test_type = forms.ChoiceField(
        choices=TEST_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the type of test to perform"
    )
    
    test_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Email address for send/receive tests (optional for connection/auth tests)"
    )
    
    test_subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Subject line for test emails"
    )
    
    test_message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        help_text="Message content for test emails"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        test_type = cleaned_data.get('test_type')
        test_email = cleaned_data.get('test_email')
        
        if test_type in ['send_test', 'receive_test'] and not test_email:
            raise forms.ValidationError("Test email address is required for send/receive tests.")
        
        return cleaned_data


class EmailNotificationForm(forms.ModelForm):
    """Form for creating email notifications"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="A descriptive name for this notification"
    )
    
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Primary recipient email address"
    )
    
    notification_type = forms.ChoiceField(
        choices=EmailNotification.NOTIFICATION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Type of notification"
    )
    
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Enter email addresses separated by commas or new lines"
    )
    
    cc_recipients = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        help_text="Enter CC email addresses separated by commas or new lines"
    )
    
    bcc_recipients = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        help_text="Enter BCC email addresses separated by commas or new lines"
    )
    
    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        help_text="When to send this notification (leave empty for immediate)"
    )
    
    class Meta:
        model = EmailNotification
        fields = [
            'name', 'notification_type', 'priority', 'subject', 'message', 
            'recipient_email', 'recipients', 'cc_recipients', 'bcc_recipients', 
            'configuration', 'scheduled_at', 'is_active'
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'configuration': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for new notifications
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['priority'].initial = 'normal'
    
    def clean_recipients(self):
        """Clean and validate recipients field"""
        recipients = self.cleaned_data.get('recipients', '')
        if not recipients:
            return []
        
        # Split by commas and newlines, clean up whitespace
        email_list = []
        for email in recipients.replace('\n', ',').split(','):
            email = email.strip()
            if email:
                email_list.append(email)
        
        # Validate each email
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        for email in email_list:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(f"Invalid email address: {email}")
        
        return email_list
    
    def clean_cc_recipients(self):
        """Clean and validate CC recipients field"""
        cc_recipients = self.cleaned_data.get('cc_recipients', '')
        if not cc_recipients:
            return []
        
        # Split by commas and newlines, clean up whitespace
        email_list = []
        for email in cc_recipients.replace('\n', ',').split(','):
            email = email.strip()
            if email:
                email_list.append(email)
        
        # Validate each email
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        for email in email_list:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(f"Invalid CC email address: {email}")
        
        return email_list
    
    def clean_bcc_recipients(self):
        """Clean and validate BCC recipients field"""
        bcc_recipients = self.cleaned_data.get('bcc_recipients', '')
        if not bcc_recipients:
            return []
        
        # Split by commas and newlines, clean up whitespace
        email_list = []
        for email in bcc_recipients.replace('\n', ',').split(','):
            email = email.strip()
            if email:
                email_list.append(email)
        
        # Validate each email
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        for email in email_list:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(f"Invalid BCC email address: {email}")
        
        return email_list
    
    def clean(self):
        """Clean and validate the form data"""
        cleaned_data = super().clean()
        
        # Ensure at least one recipient is specified
        recipient_email = cleaned_data.get('recipient_email')
        recipients = cleaned_data.get('recipients', [])
        
        if not recipient_email and not recipients:
            raise forms.ValidationError("At least one recipient email address is required.")
        
        # If recipient_email is provided, add it to recipients
        if recipient_email and recipient_email not in recipients:
            if not recipients:
                recipients = []
            recipients.append(recipient_email)
            cleaned_data['recipients'] = recipients
        
        return cleaned_data


class EmailConfigurationSearchForm(forms.Form):
    """Form for searching email configurations"""
    
    name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name...'})
    )
    
    protocol = forms.ChoiceField(
        choices=[('', 'All Protocols')] + EmailConfiguration.PROTOCOL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('success', 'Test Success'),
            ('failed', 'Test Failed'),
            ('untested', 'Untested'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    encryption = forms.ChoiceField(
        choices=[('', 'All Encryption Methods')] + EmailConfiguration.ENCRYPTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    created_by = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Created by...'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
