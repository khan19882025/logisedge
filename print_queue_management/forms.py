from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Printer, PrinterGroup, PrintTemplate, ERPEvent, 
    AutoPrintRule, PrintJob, BatchPrintJob
)


class PrinterForm(forms.ModelForm):
    """Form for creating/editing printers"""
    
    class Meta:
        model = Printer
        fields = [
            'name', 'description', 'printer_type', 'location', 
            'ip_address', 'port', 'driver_name', 'is_active', 'max_job_size'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter printer name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter printer description'}),
            'printer_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter printer location'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.100'}),
            'port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '9100'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter driver name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_job_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 1000}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        printer_type = cleaned_data.get('printer_type')
        ip_address = cleaned_data.get('ip_address')
        port = cleaned_data.get('port')
        
        if printer_type in ['network', 'cloud'] and not ip_address:
            raise ValidationError("IP address is required for network and cloud printers")
        
        if printer_type == 'network' and not port:
            raise ValidationError("Port is required for network printers")
        
        return cleaned_data


class PrinterGroupForm(forms.ModelForm):
    """Form for creating/editing printer groups"""
    
    class Meta:
        model = PrinterGroup
        fields = ['name', 'description', 'printers', 'load_balancing', 'failover', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter group name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter group description'}),
            'printers': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
            'load_balancing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'failover': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        printers = cleaned_data.get('printers')
        
        if not printers or printers.count() == 0:
            raise ValidationError("At least one printer must be selected")
        
        return cleaned_data


class PrintTemplateForm(forms.ModelForm):
    """Form for creating/editing print templates"""
    
    class Meta:
        model = PrintTemplate
        fields = [
            'name', 'template_type', 'description', 'template_file', 
            'template_content', 'variables', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter template name'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter template description'}),
            'template_file': forms.FileInput(attrs={'class': 'form-control'}),
            'template_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Enter template content or HTML'}),
            'variables': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"variable": "description"}'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_variables(self):
        variables = self.cleaned_data.get('variables')
        if variables:
            try:
                import json
                if isinstance(variables, str):
                    json.loads(variables)
                return variables
            except json.JSONDecodeError:
                raise ValidationError("Variables must be valid JSON format")
        return variables


class ERPEventForm(forms.ModelForm):
    """Form for creating/editing ERP events"""
    
    class Meta:
        model = ERPEvent
        fields = ['name', 'event_type', 'description', 'event_code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event name'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter event description'}),
            'event_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unique event code'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_event_code(self):
        event_code = self.cleaned_data.get('event_code')
        if event_code:
            # Check if event code already exists
            if ERPEvent.objects.filter(event_code=event_code).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError("Event code must be unique")
        return event_code


class AutoPrintRuleForm(forms.ModelForm):
    """Form for creating/editing auto-print rules"""
    
    class Meta:
        model = AutoPrintRule
        fields = [
            'name', 'description', 'erp_event', 'print_template', 'printer', 
            'printer_group', 'priority', 'conditions', 'batch_printing', 
            'batch_schedule', 'preview_required', 'auto_print', 
            'retry_count', 'retry_delay', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter rule name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter rule description'}),
            'erp_event': forms.Select(attrs={'class': 'form-control'}),
            'print_template': forms.Select(attrs={'class': 'form-control'}),
            'printer': forms.Select(attrs={'class': 'form-control'}),
            'printer_group': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"warehouse": "main", "customer_type": "premium"}'}),
            'batch_printing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'batch_schedule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0 8 * * 1-5 (every weekday at 8 AM)'}),
            'preview_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_print': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'retry_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'retry_delay': forms.NumberInput(attrs={'class': 'form-control', 'min': 60, 'max': 3600}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make printer and printer_group optional initially
        self.fields['printer'].required = False
        self.fields['printer_group'].required = False
        
        # Add JavaScript to handle printer/printer_group toggle
        self.fields['printer'].widget.attrs.update({
            'onchange': 'togglePrinterFields()',
            'class': 'form-control'
        })
        self.fields['printer_group'].widget.attrs.update({
            'onchange': 'togglePrinterFields()',
            'class': 'form-control'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        printer = cleaned_data.get('printer')
        printer_group = cleaned_data.get('printer_group')
        conditions = cleaned_data.get('conditions')
        
        # Validate printer assignment
        if not printer and not printer_group:
            raise ValidationError("Either printer or printer group must be specified")
        if printer and printer_group:
            raise ValidationError("Cannot specify both printer and printer group")
        
        # Validate conditions JSON
        if conditions:
            try:
                import json
                if isinstance(conditions, str):
                    json.loads(conditions)
            except json.JSONDecodeError:
                raise ValidationError("Conditions must be valid JSON format")
        
        return cleaned_data


class PrintJobForm(forms.ModelForm):
    """Form for creating/editing print jobs"""
    
    class Meta:
        model = PrintJob
        fields = [
            'print_template', 'printer', 'printer_group', 'priority', 
            'data', 'pages', 'copies', 'preview_required', 'scheduled_at'
        ]
        widgets = {
            'print_template': forms.Select(attrs={'class': 'form-control'}),
            'printer': forms.Select(attrs={'class': 'form-control'}),
            'printer_group': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"key": "value"}'}),
            'pages': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'preview_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make printer and printer_group optional initially
        self.fields['printer'].required = False
        self.fields['printer_group'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        printer = cleaned_data.get('printer')
        printer_group = cleaned_data.get('printer_group')
        data = cleaned_data.get('data')
        scheduled_at = cleaned_data.get('scheduled_at')
        
        # Validate printer assignment
        if not printer and not printer_group:
            raise ValidationError("Either printer or printer group must be specified")
        if printer and printer_group:
            raise ValidationError("Cannot specify both printer and printer group")
        
        # Validate data JSON
        if data:
            try:
                import json
                if isinstance(data, str):
                    json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError("Data must be valid JSON format")
        
        # Validate scheduled time
        if scheduled_at and scheduled_at < timezone.now():
            raise ValidationError("Scheduled time cannot be in the past")
        
        return cleaned_data


class BatchPrintJobForm(forms.ModelForm):
    """Form for creating/editing batch print jobs"""
    
    class Meta:
        model = BatchPrintJob
        fields = ['name', 'description', 'auto_print_rule', 'scheduled_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter batch job name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter batch job description'}),
            'auto_print_rule': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data.get('scheduled_at')
        if scheduled_at and scheduled_at < timezone.now():
            raise ValidationError("Scheduled time cannot be in the past")
        return scheduled_at


class PrintJobFilterForm(forms.Form):
    """Form for filtering print jobs"""
    STATUS_CHOICES = [('', 'All Statuses')] + PrintJob.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priorities')] + AutoPrintRule.PRIORITY_LEVELS
    
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
    printer = forms.ModelChoiceField(
        queryset=Printer.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    template = forms.ModelChoiceField(
        queryset=PrintTemplate.objects.filter(is_active=True),
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
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search jobs...'})
    )


class PrinterStatusForm(forms.Form):
    """Form for checking printer status"""
    printer = forms.ModelChoiceField(
        queryset=Printer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['printer'].queryset = Printer.objects.filter(is_active=True)


class ImportExportForm(forms.Form):
    """Form for importing/exporting print queue data"""
    IMPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
        ('excel', 'Excel'),
    ]
    
    EXPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
        ('excel', 'Excel'),
        ('zip', 'ZIP Archive'),
    ]
    
    import_file = forms.FileField(
        label='Import File',
        help_text='Select file to import',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    import_format = forms.ChoiceField(
        choices=IMPORT_FORMATS,
        label='File Format',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        label='Export Format',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        label='Overwrite Existing',
        help_text='Replace existing records with imported data',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    create_categories = forms.BooleanField(
        required=False,
        label='Create Missing Categories',
        help_text='Automatically create missing categories',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    dry_run = forms.BooleanField(
        required=False,
        label='Dry Run',
        help_text='Preview changes without applying them',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_inactive = forms.BooleanField(
        required=False,
        label='Include Inactive',
        help_text='Export inactive records',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_versions = forms.BooleanField(
        required=False,
        label='Include Versions',
        help_text='Export version history',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_audit_logs = forms.BooleanField(
        required=False,
        label='Include Audit Logs',
        help_text='Export audit trail',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    export_all = forms.BooleanField(
        required=False,
        label='Export All',
        help_text='Export all records',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    selected_templates = forms.ModelMultipleChoiceField(
        queryset=PrintTemplate.objects.filter(is_active=True),
        required=False,
        label='Select Templates',
        help_text='Choose specific templates to export',
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6})
    )
