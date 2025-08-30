from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Department, CostCenter, CostCenterBudget, CostCenterTransaction,
    CostCenterReport, CostCenterAuditLog
)


class DepartmentForm(forms.ModelForm):
    """Form for Department model"""
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isalnum():
            raise ValidationError("Department code must contain only letters and numbers.")
        return code.upper()


class CostCenterForm(forms.ModelForm):
    """Form for CostCenter model"""
    class Meta:
        model = CostCenter
        fields = [
            'code', 'name', 'description', 'department', 'manager',
            'parent_cost_center', 'status', 'start_date', 'end_date',
            'budget_amount', 'currency', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter cost center code'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter cost center name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'parent_cost_center': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[('AED', 'AED'), ('USD', 'USD'), ('EUR', 'EUR')]),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active departments and cost centers
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['parent_cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        self.fields['manager'].queryset = User.objects.filter(is_active=True).order_by('username')
    
    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isalnum():
            raise ValidationError("Cost center code must contain only letters and numbers.")
        return code.upper()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class CostCenterBudgetForm(forms.ModelForm):
    """Form for CostCenterBudget model"""
    class Meta:
        model = CostCenterBudget
        fields = [
            'cost_center', 'budget_period', 'start_date', 'end_date',
            'budget_amount', 'currency', 'description', 'is_active'
        ]
        widgets = {
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'budget_period': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[('AED', 'AED'), ('USD', 'USD'), ('EUR', 'EUR')]),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class CostCenterTransactionForm(forms.ModelForm):
    """Form for CostCenterTransaction model"""
    class Meta:
        model = CostCenterTransaction
        fields = [
            'cost_center', 'transaction_type', 'transaction_date',
            'reference_number', 'reference_type', 'description',
            'amount', 'currency'
        ]
        widgets = {
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reference number'}),
            'reference_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reference type'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[('AED', 'AED'), ('USD', 'USD'), ('EUR', 'EUR')]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount


class CostCenterSearchForm(forms.Form):
    """Form for searching cost centers"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by code, name, or description'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + CostCenter.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Managers",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class CostCenterBudgetSearchForm(forms.Form):
    """Form for searching cost center budgets"""
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        required=False,
        empty_label="All Cost Centers",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    budget_period = forms.ChoiceField(
        choices=[('', 'All Periods')] + CostCenterBudget.BUDGET_PERIODS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class CostCenterTransactionSearchForm(forms.Form):
    """Form for searching cost center transactions"""
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        required=False,
        empty_label="All Cost Centers",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + CostCenterTransaction.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )


class CostCenterReportForm(forms.ModelForm):
    """Form for generating cost center reports"""
    class Meta:
        model = CostCenterReport
        fields = ['report_name', 'report_type', 'cost_center', 'start_date', 'end_date']
        widgets = {
            'report_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter report name'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        self.fields['cost_center'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class CostCenterBulkUploadForm(forms.Form):
    """Form for bulk uploading cost centers"""
    file = forms.FileField(
        label='Upload CSV File',
        help_text='Upload a CSV file with cost center data. Columns: code, name, description, department_code, manager_username, status, budget_amount',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            raise ValidationError("Please upload a CSV file.")
        return file
