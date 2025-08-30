from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    NotificationTemplate, TemplateCategory, TemplatePlaceholder, 
    TemplateTest, TemplatePermission
)


class TemplateCategoryForm(forms.ModelForm):
    """Form for creating and editing template categories"""
    
    class Meta:
        model = TemplateCategory
        fields = ['name', 'description', 'color', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Choose category color'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-envelope (FontAwesome class)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class NotificationTemplateForm(forms.ModelForm):
    """Form for creating and editing notification templates"""
    
    # Additional fields for better UX
    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for changes (optional)'
        }),
        help_text="Document the reason for template changes"
    )
    
    # Test data for preview
    test_data = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Test data for placeholders"
    )
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'description', 'template_type', 'category', 'subject',
            'content', 'html_content', 'language', 'is_default_language',
            'parent_template', 'priority', 'is_active', 'requires_approval',
            'tags'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter template description'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'template_type'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email subject or SMS title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter template content with placeholders like {{customer_name}}'
            }),
            'html_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter HTML content for email templates'
            }),
            'language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_default_language': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'parent_template': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tags separated by commas'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for language field
        self.fields['language'].choices = [
            ('en', 'English'),
            ('ar', 'العربية (Arabic)'),
            ('ur', 'اردو (Urdu)'),
            ('fr', 'Français (French)'),
            ('es', 'Español (Spanish)'),
            ('de', 'Deutsch (German)'),
            ('zh', '中文 (Chinese)'),
            ('ja', '日本語 (Japanese)'),
            ('ko', '한국어 (Korean)'),
            ('hi', 'हिन्दी (Hindi)'),
        ]
        
        # Filter parent templates based on current instance
        if self.instance and self.instance.pk and hasattr(self.instance, 'category') and self.instance.category:
            self.fields['parent_template'].queryset = NotificationTemplate.objects.exclude(
                pk=self.instance.pk
            ).filter(
                template_type=self.instance.template_type,
                category=self.instance.category
            )
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.Select)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        template_type = cleaned_data.get('template_type')
        content = cleaned_data.get('content')
        html_content = cleaned_data.get('html_content')
        
        # Validate content based on template type
        if template_type == 'email':
            if not html_content:
                raise ValidationError(_("Email templates must have HTML content"))
        elif template_type == 'sms':
            if content and len(content) > 160:
                raise ValidationError(_("SMS content cannot exceed 160 characters"))
        elif template_type == 'whatsapp':
            if content and len(content) > 1000:
                raise ValidationError(_("WhatsApp content cannot exceed 1000 characters"))
        
        # Validate tags format
        tags = cleaned_data.get('tags')
        if tags:
            if isinstance(tags, str):
                # Convert comma-separated string to list
                cleaned_data['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        return cleaned_data


class TemplateTestForm(forms.ModelForm):
    """Form for testing templates"""
    
    recipient_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'test@example.com'
        }),
        help_text="Email address for testing email templates"
    )
    
    recipient_phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        }),
        help_text="Phone number for testing SMS/WhatsApp templates"
    )
    
    test_data = forms.JSONField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Test data for placeholders"
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes about this test'
        })
    )
    
    class Meta:
        model = TemplateTest
        fields = ['recipient_email', 'recipient_phone', 'test_data', 'notes']
    
    def clean(self):
        cleaned_data = super().clean()
        template = self.instance.template if self.instance else None
        
        if template:
            if template.template_type == 'email' and not cleaned_data.get('recipient_email'):
                raise ValidationError(_("Email address is required for testing email templates"))
            elif template.template_type in ['sms', 'whatsapp'] and not cleaned_data.get('recipient_phone'):
                raise ValidationError(_("Phone number is required for testing SMS/WhatsApp templates"))
        
        return cleaned_data


class TemplatePermissionForm(forms.ModelForm):
    """Form for managing template permissions"""
    
    class Meta:
        model = TemplatePermission
        fields = ['user', 'permission_type', 'category', 'is_active']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'permission_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class TemplateSearchForm(forms.Form):
    """Form for searching and filtering templates"""
    
    SEARCH_FIELDS = [
        ('name', 'Template Name'),
        ('content', 'Content'),
        ('subject', 'Subject'),
        ('description', 'Description'),
    ]
    
    SORT_OPTIONS = [
        ('name', 'Name A-Z'),
        ('-name', 'Name Z-A'),
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('-updated_at', 'Recently Updated'),
        ('template_type', 'Template Type'),
        ('category', 'Category'),
    ]
    
    # Search fields
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search templates...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        required=False,
        initial='name',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Filter fields
    template_type = forms.ChoiceField(
        choices=[('', 'All Types')] + NotificationTemplate.TEMPLATE_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=TemplateCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    language = forms.ChoiceField(
        choices=[('', 'All Languages')] + [
            ('en', 'English'),
            ('ar', 'Arabic'),
            ('ur', 'Urdu'),
            ('fr', 'French'),
            ('es', 'Spanish'),
            ('de', 'German'),
            ('zh', 'Chinese'),
            ('ja', 'Japanese'),
            ('ko', 'Korean'),
            ('hi', 'Hindi'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Sort options
    sort_by = forms.ChoiceField(
        choices=SORT_OPTIONS,
        required=False,
        initial='-updated_at',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Date range filters
    created_after = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    created_before = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Tags filter
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by tags (comma-separated)'
        })
    )


class TemplateImportForm(forms.Form):
    """Form for importing templates from external sources"""
    
    IMPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
        ('excel', 'Excel (.xlsx)'),
    ]
    
    import_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json,.csv,.xml,.xlsx'
        }),
        help_text="Select file to import templates from"
    )
    
    import_format = forms.ChoiceField(
        choices=IMPORT_FORMATS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Select the format of your import file"
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Overwrite existing templates with the same name"
    )
    
    create_categories = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Create new categories if they don't exist"
    )
    
    dry_run = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Preview import without making changes"
    )


class TemplateExportForm(forms.Form):
    """Form for exporting templates"""
    
    EXPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
        ('excel', 'Excel (.xlsx)'),
        ('zip', 'ZIP Archive'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        initial='json',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    include_inactive = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include inactive templates"
    )
    
    include_versions = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include version history"
    )
    
    include_audit_logs = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include audit trail"
    )
    
    # Template selection
    export_all = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'export_all'
        }),
        help_text="Export all templates"
    )
    
    selected_templates = forms.ModelMultipleChoiceField(
        queryset=NotificationTemplate.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text="Select specific templates to export"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selected_templates'].queryset = NotificationTemplate.objects.filter(is_active=True)
