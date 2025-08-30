from django import forms
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from .models import ImportTemplate, ImportJob, ImportValidationRule


class ImportFileUploadForm(forms.Form):
    """Form for uploading import files"""
    template = forms.ModelChoiceField(
        queryset=ImportTemplate.objects.filter(is_active=True),
        empty_label="Select a template...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'template-select'
        })
    )
    
    import_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls',
            'id': 'import-file'
        })
    )
    
    job_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a name for this import job...',
            'id': 'job-name'
        })
    )
    
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'skip-errors'
        })
    )
    
    preview_only = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'preview-only'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['template'].label = 'Import Template'
        self.fields['import_file'].label = 'File to Import'
        self.fields['job_name'].label = 'Job Name'
        self.fields['skip_errors'].label = 'Skip rows with errors'
        self.fields['preview_only'].label = 'Preview only (no import)'


class ImportTemplateForm(forms.ModelForm):
    """Form for creating and editing import templates"""
    class Meta:
        model = ImportTemplate
        fields = ['name', 'data_type', 'description', 'column_mappings', 'validation_rules', 'required_fields', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name...'
            }),
            'data_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter template description...'
            }),
            'column_mappings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter JSON column mappings...'
            }),
            'validation_rules': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter JSON validation rules...'
            }),
            'required_fields': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter comma-separated required fields...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_column_mappings(self):
        """Validate column mappings JSON"""
        column_mappings = self.cleaned_data.get('column_mappings')
        if isinstance(column_mappings, str):
            try:
                import json
                return json.loads(column_mappings)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format for column mappings")
        return column_mappings
    
    def clean_validation_rules(self):
        """Validate validation rules JSON"""
        validation_rules = self.cleaned_data.get('validation_rules')
        if isinstance(validation_rules, str):
            try:
                import json
                return json.loads(validation_rules)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format for validation rules")
        return validation_rules
    
    def clean_required_fields(self):
        """Convert required fields string to list"""
        required_fields = self.cleaned_data.get('required_fields')
        if isinstance(required_fields, str):
            return [field.strip() for field in required_fields.split(',') if field.strip()]
        return required_fields


class ImportValidationRuleForm(forms.ModelForm):
    """Form for creating and editing validation rules"""
    class Meta:
        model = ImportValidationRule
        fields = ['field_name', 'rule_type', 'validation_type', 'rule_config', 'error_message', 'is_active']
        widgets = {
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter field name...'
            }),
            'rule_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'validation_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'rule_config': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter JSON rule configuration...'
            }),
            'error_message': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter error message...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_rule_config(self):
        """Validate rule configuration JSON"""
        rule_config = self.cleaned_data.get('rule_config')
        if isinstance(rule_config, str):
            try:
                import json
                return json.loads(rule_config)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format for rule configuration")
        return rule_config


class ColumnMappingForm(forms.Form):
    """Form for mapping CSV/Excel columns to database fields"""
    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns', [])
        template_fields = kwargs.pop('template_fields', [])
        super().__init__(*args, **kwargs)
        
        for column in columns:
            self.fields[f'map_{column}'] = forms.ChoiceField(
                choices=[('', '-- Skip this column --')] + [(field, field) for field in template_fields],
                required=False,
                widget=forms.Select(attrs={
                    'class': 'form-select',
                    'data-column': column
                })
            )
            self.fields[f'map_{column}'].label = f'Map "{column}" to:'


class ImportPreviewForm(forms.Form):
    """Form for confirming import after preview"""
    confirm_import = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirm-import'
        })
    )
    
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'skip-errors'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confirm_import'].label = 'I confirm that the data looks correct and I want to proceed with the import'
        self.fields['skip_errors'].label = 'Skip rows with errors during import'


class ImportJobFilterForm(forms.Form):
    """Form for filtering import jobs"""
    STATUS_CHOICES = [('', 'All Statuses')] + ImportJob.STATUS_CHOICES
    DATA_TYPE_CHOICES = [('', 'All Data Types')] + ImportTemplate.DATA_TYPES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    data_type = forms.ChoiceField(
        choices=DATA_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by job name or file name...'
        })
    )
