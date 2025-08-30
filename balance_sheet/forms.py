from django import forms
from django.utils import timezone
from datetime import date
from .models import BalanceSheetReport, ReportTemplate
from company.company_model import Company
from chart_of_accounts.models import ChartOfAccount
from .models import AccountGroup


class BalanceSheetReportForm(forms.Form):
    """Form for generating Balance Sheet reports"""
    
    as_of_date = forms.DateField(
        label='As of Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True
        }),
        initial=timezone.now().date()
    )
    
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True),
        required=False,
        empty_label="All Companies",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    branch = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Branch (optional)'
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department (optional)'
        })
    )
    
    comparison_type = forms.ChoiceField(
        choices=[
            ('none', 'No Comparison'),
            ('previous_period', 'Previous Period'),
            ('previous_year', 'Previous Year'),
        ],
        initial='none',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    include_zero_balances = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    show_percentages = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_headers = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_totals = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_comparison = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default company if only one exists
        active_companies = Company.objects.filter(is_active=True)
        if active_companies.count() == 1:
            self.fields['company'].initial = active_companies.first()
    
    def clean_as_of_date(self):
        as_of_date = self.cleaned_data['as_of_date']
        if as_of_date > date.today():
            raise forms.ValidationError("As of date cannot be in the future.")
        return as_of_date


class ExportForm(forms.Form):
    """Form for export options"""
    
    export_format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        initial='pdf',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    include_headers = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_totals = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_comparison = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_percentages = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class AccountGroupForm(forms.ModelForm):
    """Form for managing account groups"""
    
    class Meta:
        model = AccountGroup
        fields = ['name', 'asset_type', 'parent_group', 'accounts', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_type': forms.Select(attrs={'class': 'form-control'}),
            'parent_group': forms.Select(attrs={'class': 'form-control'}),
            'accounts': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter accounts based on asset type
        if self.instance and self.instance.pk:
            self.fields['accounts'].queryset = ChartOfAccount.objects.filter(is_active=True)
        else:
            self.fields['accounts'].queryset = ChartOfAccount.objects.filter(is_active=True)


class ReportTemplateForm(forms.ModelForm):
    """Form for managing report templates"""
    
    class Meta:
        model = ReportTemplate
        fields = ['name', 'description', 'is_default', 'template_config']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'template_config': forms.HiddenInput(),
        } 