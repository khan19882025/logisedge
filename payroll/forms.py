from django import forms
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal
from multi_currency.models import Currency

from .models import (
    SalaryStructure, EmployeeSalary, BankAccount, PayrollPeriod, PayrollRecord,
    WPSRecord, EndOfServiceBenefit, Loan, Advance, GPSSARecord
)


class SalaryStructureForm(forms.ModelForm):
    """Form for creating/editing salary structures"""
    
    class Meta:
        model = SalaryStructure
        fields = ['name', 'description', 'currency', 'basic_salary', 'housing_allowance', 
                 'transport_allowance', 'other_allowances', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'housing_allowance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'transport_allowance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_allowances': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True).order_by('code')
        # Set default to AED
        if not self.instance.pk:  # Only for new instances
            aed_currency = Currency.objects.filter(code='AED').first()
            if aed_currency:
                self.fields['currency'].initial = aed_currency

    def clean(self):
        cleaned_data = super().clean()
        basic_salary = cleaned_data.get('basic_salary')
        
        if basic_salary and basic_salary <= 0:
            raise forms.ValidationError("Basic salary must be greater than zero.")
        
        return cleaned_data


class EmployeeSalaryForm(forms.ModelForm):
    """Form for creating/editing employee salary"""
    
    class Meta:
        model = EmployeeSalary
        fields = ['employee', 'salary_structure', 'currency', 'basic_salary', 'housing_allowance', 
                 'transport_allowance', 'other_allowances', 'effective_date', 'is_active']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'salary_structure': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'housing_allowance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'transport_allowance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_allowances': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter out users who already have a salary record (due to OneToOneField)
        existing_employee_ids = EmployeeSalary.objects.values_list('employee_id', flat=True)
        self.fields['employee'].queryset = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=existing_employee_ids
        ).order_by('first_name', 'last_name')
        self.fields['salary_structure'].queryset = SalaryStructure.objects.filter(is_active=True)
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True).order_by('code')
        # Set default to AED
        if not self.instance.pk:  # Only for new instances
            aed_currency = Currency.objects.filter(code='AED').first()
            if aed_currency:
                self.fields['currency'].initial = aed_currency

    def clean(self):
        cleaned_data = super().clean()
        basic_salary = cleaned_data.get('basic_salary')
        effective_date = cleaned_data.get('effective_date')
        
        if basic_salary and basic_salary <= 0:
            raise forms.ValidationError("Basic salary must be greater than zero.")
        
        if effective_date and effective_date > date.today():
            raise forms.ValidationError("Effective date cannot be in the future.")
        
        return cleaned_data


class BankAccountForm(forms.ModelForm):
    """Form for creating/editing bank account details"""
    
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_number', 'iban', 'swift_code', 'is_active']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'swift_code': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_iban(self):
        iban = self.cleaned_data.get('iban')
        if iban:
            # Basic IBAN validation for UAE (AE)
            if not iban.startswith('AE'):
                raise forms.ValidationError("IBAN must start with 'AE' for UAE accounts.")
            if len(iban) != 23:
                raise forms.ValidationError("UAE IBAN must be 23 characters long.")
        return iban


class PayrollPeriodForm(forms.ModelForm):
    """Form for creating payroll periods"""
    
    class Meta:
        model = PayrollPeriod
        fields = ['year', 'month', 'start_date', 'end_date']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2030'}),
            'month': forms.Select(choices=[
                (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
            ], attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        year = cleaned_data.get('year')
        month = cleaned_data.get('month')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        if year and month:
            # Check if period already exists
            if PayrollPeriod.objects.filter(year=year, month=month).exists():
                raise forms.ValidationError(f"Payroll period for {year}-{month:02d} already exists.")
        
        return cleaned_data


class PayrollRecordForm(forms.ModelForm):
    """Form for editing payroll records"""
    
    class Meta:
        model = PayrollRecord
        fields = [
            'basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances',
            'overtime_pay', 'bonus', 'commission', 'other_earnings',
            'loan_deduction', 'advance_deduction', 'absence_deduction', 'other_deductions',
            'working_days', 'absent_days', 'leave_days', 'overtime_hours'
        ]
        widgets = {
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'housing_allowance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'transport_allowance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_allowances': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'overtime_pay': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'commission': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_earnings': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'loan_deduction': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'advance_deduction': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'absence_deduction': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'working_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '31'}),
            'absent_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '31'}),
            'leave_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '31'}),
            'overtime_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.5'}),
        }


class WPSRecordForm(forms.ModelForm):
    """Form for WPS records"""
    
    class Meta:
        model = WPSRecord
        fields = ['company_wps_code', 'employee_wps_code', 'bank_code', 
                 'account_number', 'iban', 'salary_amount', 'status']
        widgets = {
            'company_wps_code': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_wps_code': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_code': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'salary_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class EndOfServiceBenefitForm(forms.ModelForm):
    """Form for EOSB calculation"""
    
    class Meta:
        model = EndOfServiceBenefit
        fields = [
            'contract_type', 'joining_date', 'termination_date',
            'basic_salary_for_gratuity', 'leave_encashment_days', 
            'leave_encashment_amount', 'other_benefits'
        ]
        widgets = {
            'contract_type': forms.Select(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'termination_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'basic_salary_for_gratuity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'leave_encashment_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'leave_encashment_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'other_benefits': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        joining_date = cleaned_data.get('joining_date')
        termination_date = cleaned_data.get('termination_date')
        
        if joining_date and termination_date and joining_date >= termination_date:
            raise forms.ValidationError("Termination date must be after joining date.")
        
        return cleaned_data


class LoanForm(forms.ModelForm):
    """Form for creating/editing loans"""
    
    class Meta:
        model = Loan
        fields = [
            'loan_type', 'loan_amount', 'monthly_installment', 'total_installments',
            'start_date', 'end_date', 'status'
        ]
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-control'}),
            'loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'monthly_installment': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'total_installments': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        loan_amount = cleaned_data.get('loan_amount')
        monthly_installment = cleaned_data.get('monthly_installment')
        total_installments = cleaned_data.get('total_installments')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if loan_amount and monthly_installment and total_installments:
            expected_total = monthly_installment * total_installments
            if abs(expected_total - loan_amount) > 1:  # Allow small rounding differences
                raise forms.ValidationError("Loan amount should equal monthly installment × total installments.")
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


class AdvanceForm(forms.ModelForm):
    """Form for creating/editing advances"""
    
    class Meta:
        model = Advance
        fields = ['amount', 'reason', 'requested_date', 'status']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requested_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Advance amount must be greater than zero.")
        return amount


class GPSSARecordForm(forms.ModelForm):
    """Form for GPSSA records"""
    
    class Meta:
        model = GPSSARecord
        fields = [
            'employee_contribution', 'employer_contribution',
            'emirates_id', 'passport_number', 'nationality'
        ]
        widgets = {
            'employee_contribution': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'employer_contribution': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'emirates_id': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PayrollSearchForm(forms.Form):
    """Form for searching payroll records"""
    employee = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name'),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.ChoiceField(
        choices=[('', 'All Years')] + [(year, year) for year in range(2020, 2031)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    month = forms.ChoiceField(
        choices=[('', 'All Months')] + [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + [
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('processed', 'Processed'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current year as default
        current_year = date.today().year
        self.fields['year'].choices = [('', 'All Years')] + [(year, year) for year in range(2020, current_year + 2)]


class BulkPayrollForm(forms.Form):
    """Form for bulk payroll operations"""
    payroll_period = forms.ModelChoiceField(
        queryset=PayrollPeriod.objects.filter(is_processed=False).order_by('-year', '-month'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    include_overtime = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_deductions = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class WPSExportForm(forms.Form):
    """Form for WPS export settings"""
    payroll_period = forms.ModelChoiceField(
        queryset=PayrollPeriod.objects.filter(is_processed=True).order_by('-year', '-month'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    company_wps_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    bank_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    include_all_employees = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class EOSBCalculationForm(forms.Form):
    """Form for EOSB calculation"""
    employee = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    termination_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    contract_type = forms.ChoiceField(
        choices=EndOfServiceBenefit.CONTRACT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    basic_salary_for_gratuity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
    )
    
    leave_encashment_days = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )
    
    other_benefits = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
    ) 