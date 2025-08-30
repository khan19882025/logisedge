from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    DuplicateDetectionSession, DeduplicationRule, 
    ScheduledDeduplication, DuplicateGroup
)


class DuplicateDetectionSessionForm(forms.ModelForm):
    """Form for creating and editing duplicate detection sessions"""
    
    class Meta:
        model = DuplicateDetectionSession
        fields = ['name', 'description', 'config']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter session name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the purpose of this session'
            }),
            'config': forms.HiddenInput()
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['config'].initial = {
            'entity_types': ['customer', 'vendor', 'item', 'chart_of_accounts'],
            'similarity_threshold': 0.8,
            'confidence_threshold': 0.7,
            'fuzzy_logic_enabled': True,
            'phonetic_similarity_enabled': True,
            'transaction_history_analysis': True,
            'document_link_analysis': True,
            'auto_merge_enabled': False,
            'batch_size': 1000
        }


class DeduplicationRuleForm(forms.ModelForm):
    """Form for creating and editing deduplication rules"""
    
    class Meta:
        model = DeduplicationRule
        fields = [
            'name', 'description', 'rule_type', 'entity_type',
            'similarity_threshold', 'confidence_threshold',
            'priority', 'is_active', 'rule_config'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rule name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what this rule does'
            }),
            'rule_type': forms.Select(attrs={'class': 'form-control'}),
            'entity_type': forms.Select(attrs={'class': 'form-control'}),
            'similarity_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1,
                'step': 0.01
            }),
            'confidence_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1,
                'step': 0.01
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rule_config': forms.HiddenInput()
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Entity type choices
        self.fields['entity_type'].choices = [
            ('customer', 'Customer'),
            ('vendor', 'Vendor'),
            ('item', 'Inventory Item'),
            ('chart_of_accounts', 'Chart of Accounts'),
            ('employee', 'Employee'),
            ('asset', 'Asset'),
            ('location', 'Location'),
        ]
        
        # Set default rule configuration based on rule type
        if self.instance.pk:
            rule_config = self.instance.rule_config
        else:
            rule_config = self.get_default_rule_config()
        
        self.fields['rule_config'].initial = rule_config
    
    def get_default_rule_config(self):
        """Get default configuration based on rule type"""
        rule_type = self.data.get('rule_type') if self.data else None
        
        if rule_type == 'exact_match':
            return {
                'fields': ['name', 'email', 'phone'],
                'case_sensitive': False,
                'ignore_whitespace': True
            }
        elif rule_type == 'fuzzy_match':
            return {
                'fields': ['name', 'description'],
                'algorithm': 'levenshtein',
                'max_distance': 3,
                'weighted_fields': True
            }
        elif rule_type == 'phonetic_match':
            return {
                'fields': ['name'],
                'algorithm': 'metaphone',
                'min_length': 3
            }
        else:
            return {
                'fields': [],
                'custom_logic': ''
            }


class ScheduledDeduplicationForm(forms.ModelForm):
    """Form for creating and editing scheduled deduplication tasks"""
    
    class Meta:
        model = ScheduledDeduplication
        fields = [
            'name', 'description', 'schedule_type', 'cron_expression',
            'is_active', 'config'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter schedule name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this scheduled task'
            }),
            'schedule_type': forms.Select(attrs={'class': 'form-control'}),
            'cron_expression': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0 2 * * * (for daily at 2 AM)'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config': forms.HiddenInput()
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default configuration
        if not self.instance.pk:
            self.fields['config'].initial = {
                'entity_types': ['customer', 'vendor'],
                'similarity_threshold': 0.8,
                'confidence_threshold': 0.7,
                'auto_merge': False,
                'notify_on_completion': True,
                'max_execution_time': 3600  # 1 hour
            }
    
    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get('schedule_type')
        cron_expression = cleaned_data.get('cron_expression')
        
        if schedule_type == 'custom' and not cron_expression:
            raise ValidationError("Cron expression is required for custom schedules")
        
        if cron_expression:
            # Basic cron expression validation
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValidationError("Cron expression must have 5 parts: minute hour day month weekday")
        
        return cleaned_data


class MergeConfigurationForm(forms.Form):
    """Form for configuring merge operations"""
    
    # Entity type selection
    entity_types = forms.MultipleChoiceField(
        choices=[
            ('customer', 'Customers'),
            ('vendor', 'Vendors'),
            ('item', 'Inventory Items'),
            ('chart_of_accounts', 'Chart of Accounts'),
            ('employee', 'Employees'),
            ('asset', 'Assets'),
            ('location', 'Locations'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        initial=['customer', 'vendor', 'item']
    )
    
    # Detection settings
    similarity_threshold = forms.DecimalField(
        min_value=0.0,
        max_value=1.0,
        decimal_places=2,
        initial=0.8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01,
            'min': 0,
            'max': 1
        })
    )
    
    confidence_threshold = forms.DecimalField(
        min_value=0.0,
        max_value=1.0,
        decimal_places=2,
        initial=0.7,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01,
            'min': 0,
            'max': 1
        })
    )
    
    # Algorithm settings
    fuzzy_logic_enabled = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    phonetic_similarity_enabled = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Analysis settings
    transaction_history_analysis = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    document_link_analysis = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Merge settings
    auto_merge_enabled = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    batch_size = forms.IntegerField(
        min_value=100,
        max_value=10000,
        initial=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 100,
            'max': 10000
        })
    )
    
    # Master record selection criteria
    completeness_weight = forms.DecimalField(
        min_value=0.0,
        max_value=1.0,
        decimal_places=2,
        initial=0.4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01,
            'min': 0,
            'max': 1
        })
    )
    
    recency_weight = forms.DecimalField(
        min_value=0.0,
        max_value=1.0,
        decimal_places=2,
        initial=0.3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01,
            'min': 0,
            'max': 1
        })
    )
    
    data_quality_weight = forms.DecimalField(
        min_value=0.0,
        max_value=1.0,
        decimal_places=2,
        initial=0.3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01,
            'min': 0,
            'max': 1
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that weights sum to 1.0
        completeness = cleaned_data.get('completeness_weight', 0)
        recency = cleaned_data.get('recency_weight', 0)
        quality = cleaned_data.get('data_quality_weight', 0)
        
        total_weight = completeness + recency + quality
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point differences
            raise ValidationError("Master record selection weights must sum to 1.0")
        
        return cleaned_data


class DuplicateGroupReviewForm(forms.Form):
    """Form for reviewing and approving duplicate groups for merging"""
    
    duplicate_group_id = forms.IntegerField(widget=forms.HiddenInput())
    
    # Master record selection
    master_record_id = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text="Select the record that will become the master record after merging"
    )
    
    # Merge confirmation
    confirm_merge = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="I confirm that I want to merge these duplicate records"
    )
    
    # Additional notes
    merge_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes about this merge decision'
        })
    )
    
    def __init__(self, duplicate_group=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if duplicate_group:
            # Populate master record choices
            records = duplicate_group.duplicaterecord_set.all().order_by('-overall_score')
            choices = [(record.id, f"{record.record_id} (Score: {record.overall_score})") 
                      for record in records]
            self.fields['master_record_id'].choices = choices


class BulkMergeForm(forms.Form):
    """Form for bulk merge operations"""
    
    # Selection criteria
    entity_type = forms.ChoiceField(
        choices=[
            ('customer', 'Customers'),
            ('vendor', 'Vendors'),
            ('item', 'Inventory Items'),
            ('chart_of_accounts', 'Chart of Accounts'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    confidence_threshold = forms.DecimalField(
        min_value=0.0,
        max_value=1.0,
        decimal_places=2,
        initial=0.9,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01,
            'min': 0,
            'max': 1
        }),
        help_text="Only merge duplicates with confidence above this threshold"
    )
    
    max_duplicates_per_group = forms.IntegerField(
        min_value=2,
        max_value=10,
        initial=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 2,
            'max': 10
        }),
        help_text="Maximum number of duplicates to merge in a single group"
    )
    
    # Execution settings
    dry_run = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Preview changes without actually merging (recommended)"
    )
    
    notify_on_completion = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
