from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .models import (
    ExitType, ClearanceDepartment, ClearanceItem, ResignationRequest,
    ClearanceProcess, ClearanceItemStatus, GratuityCalculation,
    FinalSettlement, ExitDocument, ExitConfiguration
)
from employees.models import Employee


class ExitTypeForm(forms.ModelForm):
    """Form for creating and editing exit types"""
    class Meta:
        model = ExitType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClearanceDepartmentForm(forms.ModelForm):
    """Form for creating and editing clearance departments"""
    class Meta:
        model = ClearanceDepartment
        fields = ['name', 'description', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ClearanceItemForm(forms.ModelForm):
    """Form for creating and editing clearance items"""
    class Meta:
        model = ClearanceItem
        fields = ['department', 'name', 'description', 'is_required', 'is_active', 'order']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ResignationRequestForm(forms.ModelForm):
    """Form for creating resignation requests"""
    class Meta:
        model = ResignationRequest
        fields = [
            'employee', 'exit_type', 'contract_type', 'resignation_date',
            'last_working_day', 'notice_period_days', 'notice_period_served', 
            'reason', 'additional_comments', 'manager', 'hr_manager',
            'resignation_letter'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'exit_type': forms.Select(attrs={'class': 'form-select'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'resignation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_working_day': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notice_period_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notice_period_served': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Please provide detailed reason for resignation...'}),
            'additional_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any additional information or special circumstances...'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'hr_manager': forms.Select(attrs={'class': 'form-select'}),
            'resignation_letter': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active employees
        self.fields['employee'].queryset = Employee.objects.filter(status='active')
        self.fields['exit_type'].queryset = ExitType.objects.filter(is_active=True)
        
        # Set empty labels
        self.fields['manager'].empty_label = "Select Manager"
        self.fields['hr_manager'].empty_label = "Select HR Manager"

    def clean(self):
        cleaned_data = super().clean()
        resignation_date = cleaned_data.get('resignation_date')
        last_working_day = cleaned_data.get('last_working_day')
        
        if resignation_date and last_working_day:
            if resignation_date > last_working_day:
                raise forms.ValidationError("Last working day cannot be before resignation date.")
            
            if resignation_date < timezone.now().date():
                raise forms.ValidationError("Resignation date cannot be in the past.")
        
        return cleaned_data


class ResignationApprovalForm(forms.ModelForm):
    """Form for manager/HR approval of resignation requests"""
    class Meta:
        model = ResignationRequest
        fields = ['manager_comments', 'hr_comments']
        widgets = {
            'manager_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hr_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ClearanceItemStatusForm(forms.ModelForm):
    """Form for updating clearance item status"""
    class Meta:
        model = ClearanceItemStatus
        fields = ['status', 'comments']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class GratuityCalculationForm(forms.ModelForm):
    """Form for gratuity calculation"""
    class Meta:
        model = GratuityCalculation
        fields = [
            'basic_salary', 'total_years_service', 'contract_type',
            'notice_period_deduction', 'other_deductions', 'notes'
        ]
        widgets = {
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_years_service': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'notice_period_deduction': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        resignation = kwargs.pop('resignation', None)
        super().__init__(*args, **kwargs)
        if resignation:
            # Pre-fill with employee data
            employee = resignation.employee
            if employee.salary:
                self.fields['basic_salary'].initial = employee.salary
            
            # Calculate years of service
            if employee.date_of_joining:
                years_service = (timezone.now().date() - employee.date_of_joining).days / 365.25
                self.fields['total_years_service'].initial = round(years_service, 2)
            
            self.fields['contract_type'].initial = resignation.contract_type


class FinalSettlementForm(forms.ModelForm):
    """Form for final settlement calculation"""
    class Meta:
        model = FinalSettlement
        fields = [
            'last_month_salary', 'leave_encashment', 'loan_deductions',
            'notice_period_deduction', 'other_deductions'
        ]
        widgets = {
            'last_month_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'leave_encashment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'loan_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notice_period_deduction': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ExitDocumentForm(forms.ModelForm):
    """Form for generating exit documents"""
    class Meta:
        model = ExitDocument
        fields = ['document_type', 'title', 'is_bilingual']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_bilingual': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExitConfigurationForm(forms.ModelForm):
    """Form for exit management configuration"""
    class Meta:
        model = ExitConfiguration
        fields = ['key', 'value', 'description', 'is_active']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResignationSearchForm(forms.Form):
    """Form for searching resignation requests"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by employee name, reference number...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + ResignationRequest.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    exit_type = forms.ModelChoiceField(
        queryset=ExitType.objects.filter(is_active=True),
        required=False,
        empty_label="All Exit Types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    department = forms.ModelChoiceField(
        queryset=Employee.objects.values_list('department', flat=True).distinct(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ClearanceSearchForm(forms.Form):
    """Form for searching clearance processes"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by employee name...'
        })
    )
    department = forms.ModelChoiceField(
        queryset=ClearanceDepartment.objects.filter(is_active=True),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class GratuitySearchForm(forms.Form):
    """Form for searching gratuity calculations"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by employee name...'
        })
    )
    contract_type = forms.ChoiceField(
        choices=[('', 'All Contract Types')] + ResignationRequest.CONTRACT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Amount'})
    )
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Amount'})
    )


class SettlementSearchForm(forms.Form):
    """Form for searching final settlements"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by employee name...'
        })
    )
    is_processed = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('True', 'Processed'),
            ('False', 'Not Processed'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class BulkClearanceForm(forms.Form):
    """Form for bulk clearance operations"""
    clearance_items = forms.ModelMultipleChoiceField(
        queryset=ClearanceItem.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    status = forms.ChoiceField(
        choices=ClearanceItemStatus.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class NoticePeriodCalculationForm(forms.Form):
    """Form for calculating notice period"""
    resignation_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    notice_period_days = forms.IntegerField(
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    last_working_day = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def clean(self):
        cleaned_data = super().clean()
        resignation_date = cleaned_data.get('resignation_date')
        last_working_day = cleaned_data.get('last_working_day')
        
        if resignation_date and last_working_day:
            if resignation_date > last_working_day:
                raise forms.ValidationError("Last working day cannot be before resignation date.")
        
        return cleaned_data


class ExitReportForm(forms.Form):
    """Form for generating exit reports"""
    REPORT_TYPE_CHOICES = [
        ('attrition', 'Attrition Report'),
        ('gratuity', 'Gratuity Summary'),
        ('clearance', 'Clearance Status'),
        ('settlement', 'Settlement Summary'),
        ('exit_reasons', 'Exit Reasons Trend'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    department = forms.ModelChoiceField(
        queryset=Employee.objects.values_list('department', flat=True).distinct(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    export_format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    ) 