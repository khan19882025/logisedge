from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

from .models import (
    BudgetPlan, BudgetItem, BudgetTemplate, BudgetTemplateItem,
    BudgetApproval, BudgetImport, BudgetAuditLog, BudgetVarianceAlert,
    BudgetVarianceNotification, BudgetVsActualReport
)
from cost_center_management.models import CostCenter, Department
from chart_of_accounts.models import ChartOfAccount


class BudgetPlanForm(forms.ModelForm):
    """Form for creating and editing budget plans"""
    
    class Meta:
        model = BudgetPlan
        fields = [
            'budget_code', 'budget_name', 'fiscal_year', 'budget_period',
            'start_date', 'end_date', 'total_budget_amount', 'currency', 'notes'
        ]
        widgets = {
            'budget_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique budget code'
            }),
            'budget_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter budget name'
            }),
            'fiscal_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024'
            }),
            'budget_period': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_budget_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('AED', 'AED - UAE Dirham'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
            ]),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter budget notes and justification'
            }),
        }
    
    def clean_budget_code(self):
        budget_code = self.cleaned_data['budget_code']
        if BudgetPlan.objects.filter(budget_code=budget_code).exists():
            if self.instance.pk:
                # Editing existing budget
                if BudgetPlan.objects.filter(budget_code=budget_code).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("This budget code already exists.")
            else:
                # Creating new budget
                raise forms.ValidationError("This budget code already exists.")
        return budget_code
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


class BudgetItemForm(forms.ModelForm):
    """Form for creating and editing budget items"""
    
    class Meta:
        model = BudgetItem
        fields = [
            'cost_center', 'department', 'account', 'budget_amount', 'notes'
        ]
        widgets = {
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'budget_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter notes for this budget item'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active cost centers and departments
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['account'].queryset = ChartOfAccount.objects.filter(is_active=True)


class BudgetItemBulkForm(forms.Form):
    """Form for bulk creating budget items"""
    cost_centers = forms.ModelMultipleChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    accounts = forms.ModelMultipleChoiceField(
        queryset=ChartOfAccount.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    default_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        })
    )


class BudgetApprovalForm(forms.ModelForm):
    """Form for budget approval workflow"""
    
    class Meta:
        model = BudgetApproval
        fields = ['approval_type', 'comments']
        widgets = {
            'approval_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter approval comments'
            }),
        }


class BudgetTemplateForm(forms.ModelForm):
    """Form for creating and editing budget templates"""
    
    class Meta:
        model = BudgetTemplate
        fields = ['template_name', 'description', 'fiscal_year', 'budget_period']
        widgets = {
            'template_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter template description'
            }),
            'fiscal_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024'
            }),
            'budget_period': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class BudgetTemplateItemForm(forms.ModelForm):
    """Form for creating and editing budget template items"""
    
    class Meta:
        model = BudgetTemplateItem
        fields = ['cost_center', 'account', 'default_amount', 'notes']
        widgets = {
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'default_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter notes for this template item'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        self.fields['account'].queryset = ChartOfAccount.objects.filter(is_active=True)


class BudgetSearchForm(forms.Form):
    """Form for searching budgets"""
    budget_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by budget code'
        })
    )
    budget_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by budget name'
        })
    )
    fiscal_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Fiscal year'
        })
    )
    budget_period = forms.ChoiceField(
        choices=[('', 'All Periods')] + BudgetPlan.BUDGET_PERIODS,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + BudgetPlan.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class BudgetImportForm(forms.Form):
    """Form for importing budgets from Excel"""
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload an Excel file (.xlsx or .xls) with budget data',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 10MB.")
            
            # Check file extension
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError("Please upload an Excel file (.xlsx or .xls).")
        
        return file


class BudgetVarianceReportForm(forms.Form):
    """Form for generating budget variance reports"""
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('department', 'Department Report'),
        ('cost_center', 'Cost Center Report'),
    ]
    
    PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='summary'
    )
    period = forms.ChoiceField(
        choices=PERIODS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='monthly'
    )
    fiscal_year = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2024'
        }),
        initial=timezone.now().year
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    include_zero_budgets = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BudgetVarianceAlertForm(forms.ModelForm):
    """Form for creating and editing budget variance alerts"""
    
    class Meta:
        model = BudgetVarianceAlert
        fields = [
            'alert_name', 'alert_type', 'severity', 'threshold_percentage',
            'threshold_amount', 'cost_center', 'department', 'is_active',
            'notify_finance_managers', 'notify_department_heads', 'notify_users'
        ]
        widgets = {
            'alert_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter alert name'
            }),
            'alert_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'threshold_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'e.g., 10.00 for 10%'
            }),
            'threshold_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'e.g., 1000.00'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_finance_managers': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_department_heads': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notify_users': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['notify_users'].queryset = User.objects.filter(is_active=True)


class BudgetVsActualReportForm(forms.Form):
    """Form for generating Budget vs Actual reports"""
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('department', 'Department Report'),
        ('cost_center', 'Cost Center Report'),
        ('variance', 'Variance Report'),
    ]
    
    PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Period'),
    ]
    
    report_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter report name'
        })
    )
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='summary'
    )
    fiscal_year = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2024'
        }),
        initial=timezone.now().year
    )
    period = forms.ChoiceField(
        choices=PERIODS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='monthly'
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    include_zero_budgets = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_inactive = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        period = cleaned_data.get('period')
        
        if period == 'custom':
            if not start_date or not end_date:
                raise forms.ValidationError("Start date and end date are required for custom period.")
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


class BudgetVarianceNotificationForm(forms.ModelForm):
    """Form for creating variance notifications"""
    
    class Meta:
        model = BudgetVarianceNotification
        fields = ['notification_type', 'subject', 'message']
        widgets = {
            'notification_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notification subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter notification message'
            }),
        }
