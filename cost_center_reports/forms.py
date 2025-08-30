from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import CostCenterFinancialReport, CostCenterReportFilter, CostCenterReportExport, CostCenterReportSchedule
from cost_center_management.models import CostCenter, Department


class CostCenterFinancialReportForm(forms.ModelForm):
    """Form for creating and editing cost center financial reports"""
    
    class Meta:
        model = CostCenterFinancialReport
        fields = [
            'report_name', 'report_type', 'start_date', 'end_date', 
            'cost_center', 'department', 'include_inactive'
        ]
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'report_type': forms.Select(attrs={
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
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'include_inactive': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active cost centers and departments
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        # Set default dates
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['start_date'].initial = today.replace(day=1)  # First day of current month
            self.fields['end_date'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


class CostCenterReportFilterForm(forms.ModelForm):
    """Form for report filters"""
    
    class Meta:
        model = CostCenterReportFilter
        fields = ['filter_name', 'filter_value', 'filter_type']
        widgets = {
            'filter_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Filter name'
            }),
            'filter_value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Filter value'
            }),
            'filter_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class CostCenterReportSearchForm(forms.Form):
    """Form for searching and filtering reports"""
    report_type = forms.ChoiceField(
        choices=[('', 'All Types')] + CostCenterFinancialReport.REPORT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
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
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + CostCenterFinancialReport.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CostCenterReportExportForm(forms.ModelForm):
    """Form for exporting reports"""
    
    class Meta:
        model = CostCenterReportExport
        fields = ['export_type']
        widgets = {
            'export_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class CostCenterReportScheduleForm(forms.ModelForm):
    """Form for scheduling reports"""
    
    class Meta:
        model = CostCenterReportSchedule
        fields = [
            'schedule_name', 'report_type', 'frequency', 
            'start_date', 'end_date', 'is_active', 'recipients'
        ]
        widgets = {
            'schedule_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter schedule name'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'frequency': forms.Select(attrs={
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
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'recipients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter email addresses (one per line)'
            }),
        }
    
    def clean_recipients(self):
        recipients = self.cleaned_data.get('recipients')
        if recipients:
            # Convert textarea input to list
            email_list = [email.strip() for email in recipients.split('\n') if email.strip()]
            # Basic email validation
            for email in email_list:
                if '@' not in email or '.' not in email:
                    raise forms.ValidationError(f"Invalid email address: {email}")
            return email_list
        return []
