from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import FiscalYear, FiscalPeriod, FiscalSettings


class FiscalYearForm(forms.ModelForm):
    """Form for creating and editing fiscal years"""
    
    class Meta:
        model = FiscalYear
        fields = ['name', 'start_date', 'end_date', 'is_current', 'status', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., FY 2024-25'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Additional description or notes...'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            # Check for overlapping fiscal years
            overlapping = FiscalYear.objects.filter(
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            
            if overlapping.exists():
                raise ValidationError("Fiscal year dates overlap with existing fiscal year")
        
        return cleaned_data


class FiscalPeriodForm(forms.ModelForm):
    """Form for creating and editing fiscal periods"""
    
    class Meta:
        model = FiscalPeriod
        fields = ['fiscal_year', 'name', 'start_date', 'end_date', 'period_type', 'status', 'is_current', 'description']
        widgets = {
            'fiscal_year': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Q1, January'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Additional description or notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active fiscal years
        self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(status__in=['active', 'inactive'])
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        fiscal_year = cleaned_data.get('fiscal_year')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            # Check if period is within fiscal year
            if fiscal_year:
                if start_date < fiscal_year.start_date or end_date > fiscal_year.end_date:
                    raise ValidationError("Period must be within the fiscal year dates")
            
            # Check for overlapping periods within the same fiscal year
            if fiscal_year:
                overlapping = FiscalPeriod.objects.filter(
                    fiscal_year=fiscal_year,
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                if self.instance.pk:
                    overlapping = overlapping.exclude(pk=self.instance.pk)
                
                if overlapping.exists():
                    raise ValidationError("Period dates overlap with existing period in the same fiscal year")
        
        return cleaned_data


class FiscalSettingsForm(forms.ModelForm):
    """Form for fiscal year settings"""
    
    class Meta:
        model = FiscalSettings
        fields = [
            'default_fiscal_year_start_month',
            'default_period_type',
            'auto_create_periods',
            'allow_overlapping_periods',
            'require_period_approval',
            'fiscal_year_naming_convention',
            'period_naming_convention'
        ]
        widgets = {
            'default_fiscal_year_start_month': forms.Select(attrs={'class': 'form-control'}),
            'default_period_type': forms.Select(attrs={'class': 'form-control'}),
            'fiscal_year_naming_convention': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., FY {start_year}-{end_year}'
            }),
            'period_naming_convention': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., {period_type} {period_number}'
            }),
        }


class FiscalYearSearchForm(forms.Form):
    """Form for searching fiscal years"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or description...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + FiscalYear.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_current = forms.BooleanField(
        required=False,
        label='Current Fiscal Year Only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    start_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    start_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class FiscalPeriodSearchForm(forms.Form):
    """Form for searching fiscal periods"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or description...'
        })
    )
    
    fiscal_year = forms.ModelChoiceField(
        queryset=FiscalYear.objects.all(),
        required=False,
        empty_label="All Fiscal Years",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    period_type = forms.ChoiceField(
        choices=[('', 'All Types')] + FiscalPeriod.PERIOD_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + FiscalPeriod.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_current = forms.BooleanField(
        required=False,
        label='Current Period Only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    ) 