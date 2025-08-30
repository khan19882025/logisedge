from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import AssetMovementLog, AssetMovementTemplate, AssetMovementSettings


class AssetMovementLogForm(forms.ModelForm):
    """Form for creating and editing asset movement logs"""
    
    class Meta:
        model = AssetMovementLog
        fields = [
            'asset', 'movement_type', 'movement_date', 'movement_reason', 
            'reason_description', 'from_location', 'to_location', 'from_user', 
            'to_user', 'notes', 'estimated_duration', 'actual_return_date',
            'is_completed', 'is_approved'
        ]
        widgets = {
            'movement_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'actual_return_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'reason_description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'notes': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
            'estimated_duration': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'max': '365'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required based on settings
        settings = AssetMovementSettings.get_settings()
        if settings.require_reason:
            self.fields['reason_description'].required = True
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        movement_date = cleaned_data.get('movement_date')
        actual_return_date = cleaned_data.get('actual_return_date')
        estimated_duration = cleaned_data.get('estimated_duration')
        
        # Validate return date is after movement date
        if actual_return_date and movement_date:
            if actual_return_date <= movement_date:
                raise forms.ValidationError(
                    "Actual return date must be after movement date."
                )
        
        # Validate estimated duration
        if estimated_duration:
            settings = AssetMovementSettings.get_settings()
            if estimated_duration > settings.max_duration_days:
                raise forms.ValidationError(
                    f"Estimated duration cannot exceed {settings.max_duration_days} days."
                )
        
        return cleaned_data


class AssetMovementLogSearchForm(forms.Form):
    """Form for searching and filtering asset movement logs"""
    
    # Search fields
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by asset code, name, or notes...'
        })
    )
    
    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    # Filter fields
    movement_type = forms.ChoiceField(
        choices=[('', 'All Types')] + AssetMovementLog.MOVEMENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    movement_reason = forms.ChoiceField(
        choices=[('', 'All Reasons')] + AssetMovementLog.MOVEMENT_REASONS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    from_location = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All From Locations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    to_location = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All To Locations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    moved_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_completed = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Completed'), ('False', 'Pending')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_approved = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Approved'), ('False', 'Pending Approval')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set querysets for location fields
        from asset_register.models import AssetLocation
        self.fields['from_location'].queryset = AssetLocation.objects.filter(is_active=True)
        self.fields['to_location'].queryset = AssetLocation.objects.filter(is_active=True)


class AssetMovementLogExportForm(forms.Form):
    """Form for exporting asset movement logs"""
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        initial='excel',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    date_range = forms.ChoiceField(
        choices=[
            ('all', 'All Time'),
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('quarter', 'This Quarter'),
            ('year', 'This Year'),
            ('custom', 'Custom Range'),
        ],
        initial='month',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    custom_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    custom_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )


class AssetMovementTemplateForm(forms.ModelForm):
    """Form for creating and editing asset movement templates"""
    
    class Meta:
        model = AssetMovementTemplate
        fields = ['name', 'description', 'movement_type', 'movement_reason', 
                 'default_notes', 'estimated_duration', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'default_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '365'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})


class AssetMovementSettingsForm(forms.ModelForm):
    """Form for asset movement settings"""
    
    class Meta:
        model = AssetMovementSettings
        fields = ['require_approval', 'auto_approve_assignments', 'require_reason', 
                 'max_duration_days', 'enable_notifications']
        widgets = {
            'max_duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '3650'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class QuickMovementForm(forms.ModelForm):
    """Quick form for creating asset movements"""
    
    class Meta:
        model = AssetMovementLog
        fields = ['asset', 'movement_type', 'to_location', 'to_user', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
        
        # Set current user as moved_by
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        kwargs['initial']['moved_by'] = self.request.user if hasattr(self, 'request') else None
