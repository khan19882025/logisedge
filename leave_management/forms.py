from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    LeaveRequest, LeaveType, LeaveBalance, LeaveApproval, 
    LeavePolicy, LeaveEncashment, LeaveNotification
)


class LeaveRequestForm(forms.ModelForm):
    """Form for submitting leave requests"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().isoformat()
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().isoformat()
        })
    )
    is_half_day = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    half_day_type = forms.ChoiceField(
        choices=[('', 'Select half day type'), ('morning', 'Morning'), ('afternoon', 'Afternoon')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_emergency = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type', 'start_date', 'end_date', 'reason', 
            'priority', 'attachment', 'is_half_day', 'half_day_type', 'is_emergency'
        ]
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide a detailed reason for your leave request...'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter active leave types
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        
        # Check if user has HR/manager permissions
        can_create_for_others = (
            self.user and (
                self.user.is_superuser or 
                self.user.has_perm('leave_management.can_manage_leave_types') or
                self.user.has_perm('leave_management.can_approve_leave') or
                self.user.groups.filter(name__in=['HR', 'Managers', 'Administrators']).exists()
            )
        )
        
        if can_create_for_others:
            # Add employee selection field for HR/managers
            self.fields['employee'] = forms.ModelChoiceField(
                queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name'),
                empty_label="Select Employee",
                widget=forms.Select(attrs={
                    'class': 'form-select',
                    'required': 'required'
                }),
                label="Employee"
            )
            # Make employee field required
            self.fields['employee'].required = True
        else:
            # For regular employees, set employee to current user (hidden field)
            if self.user:
                self.fields['employee'] = forms.ModelChoiceField(
                    queryset=User.objects.filter(id=self.user.id),
                    initial=self.user,
                    widget=forms.HiddenInput()
                )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')
        is_half_day = cleaned_data.get('is_half_day')
        half_day_type = cleaned_data.get('half_day_type')
        employee = cleaned_data.get('employee')

        if start_date and end_date:
            # Check if end date is after start date
            if end_date < start_date:
                raise ValidationError("End date cannot be before start date.")

            # Check if dates are in the past
            if start_date < date.today():
                raise ValidationError("Cannot apply for leave in the past.")

            # Check minimum notice period
            if leave_type and leave_type.min_notice_days > 0:
                min_notice_date = date.today() + timedelta(days=leave_type.min_notice_days)
                if start_date < min_notice_date and not cleaned_data.get('is_emergency'):
                    raise ValidationError(
                        f"Leave must be applied at least {leave_type.min_notice_days} days in advance "
                        f"(except for emergency leaves)."
                    )

            # Check leave balance
            if employee and leave_type:
                try:
                    balance = LeaveBalance.objects.get(
                        employee=employee,
                        leave_type=leave_type,
                        year=date.today().year
                    )
                    
                    # Calculate required days
                    required_days = self._calculate_leave_days(start_date, end_date, is_half_day, half_day_type)
                    
                    if balance.available_days < required_days:
                        raise ValidationError(
                            f"Insufficient leave balance. Available: {balance.available_days} days, "
                            f"Required: {required_days} days."
                        )
                except LeaveBalance.DoesNotExist:
                    raise ValidationError(f"No leave balance found for {leave_type.name}.")

        return cleaned_data

    def _calculate_leave_days(self, start_date, end_date, is_half_day, half_day_type):
        """Calculate the number of leave days required"""
        if not start_date or not end_date:
            return 0
            
        # Calculate business days (excluding weekends)
        current_date = start_date
        business_days = 0
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday to Friday
                business_days += 1
            current_date += timedelta(days=1)
        
        # Adjust for half days
        if is_half_day:
            if half_day_type == 'morning' and start_date == end_date:
                business_days = 0.5
            elif half_day_type == 'afternoon' and start_date == end_date:
                business_days = 0.5
            else:
                # For multi-day half-day leaves, reduce by 0.5
                business_days -= 0.5
        
        return business_days

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set employee if not already set
        if not instance.employee:
            if self.user and not self.user.has_perm('leave_management.can_manage_leave_types'):
                instance.employee = self.user
            else:
                instance.employee = self.cleaned_data.get('employee')
        
        if commit:
            instance.save()
        return instance


class LeaveApprovalForm(forms.ModelForm):
    """Form for approving/rejecting leave requests"""
    action = forms.ChoiceField(
        choices=LeaveApproval.ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add your comments or feedback...'
        })
    )

    class Meta:
        model = LeaveApproval
        fields = ['action', 'comments']

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        comments = cleaned_data.get('comments')

        # Require comments for rejections
        if action == 'reject' and not comments.strip():
            raise ValidationError("Comments are required when rejecting a leave request.")

        return cleaned_data


class LeaveBalanceForm(forms.ModelForm):
    """Form for managing leave balances"""
    class Meta:
        model = LeaveBalance
        fields = ['allocated_days', 'used_days', 'carried_forward_days', 'encashed_days']
        widgets = {
            'allocated_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'used_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'carried_forward_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'encashed_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        allocated_days = cleaned_data.get('allocated_days', 0)
        used_days = cleaned_data.get('used_days', 0)
        carried_forward_days = cleaned_data.get('carried_forward_days', 0)
        encashed_days = cleaned_data.get('encashed_days', 0)

        # Validate that used days don't exceed total balance
        total_balance = allocated_days + carried_forward_days
        if used_days + encashed_days > total_balance:
            raise ValidationError(
                "Used days and encashed days cannot exceed total allocated balance."
            )

        return cleaned_data


class LeaveTypeForm(forms.ModelForm):
    """Form for creating/editing leave types"""
    class Meta:
        model = LeaveType
        fields = [
            'name', 'description', 'color', 'is_active', 'requires_approval',
            'max_days_per_year', 'max_consecutive_days', 'min_notice_days',
            'is_paid', 'can_carry_forward', 'max_carry_forward_days'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_days_per_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'max_consecutive_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'min_notice_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_carry_forward': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_carry_forward_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }


class LeavePolicyForm(forms.ModelForm):
    """Form for creating/editing leave policies"""
    class Meta:
        model = LeavePolicy
        fields = [
            'name', 'description', 'probation_period_months',
            'annual_leave_days', 'sick_leave_days', 'casual_leave_days',
            'maternity_leave_days', 'paternity_leave_days',
            'carry_forward_percentage', 'encashment_allowed',
            'encashment_percentage', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'probation_period_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'annual_leave_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'sick_leave_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'casual_leave_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'maternity_leave_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'paternity_leave_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'carry_forward_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'encashment_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'encashment_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LeaveEncashmentForm(forms.ModelForm):
    """Form for leave encashment requests"""
    class Meta:
        model = LeaveEncashment
        fields = ['leave_type', 'encashment_year', 'days_to_encash', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'encashment_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': date.today().year - 1,
                'max': date.today().year
            }),
            'days_to_encash': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.5'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please provide a reason for encashment...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter leave types that allow encashment
            self.fields['leave_type'].queryset = LeaveType.objects.filter(
                is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        encashment_year = cleaned_data.get('encashment_year')
        days_to_encash = cleaned_data.get('days_to_encash')

        if self.user and leave_type and encashment_year and days_to_encash:
            # Check if user has sufficient balance
            balance = LeaveBalance.objects.filter(
                employee=self.user,
                leave_type=leave_type,
                year=encashment_year
            ).first()

            if not balance or balance.available_days < days_to_encash:
                raise ValidationError(
                    f"Insufficient leave balance for encashment. "
                    f"Available: {balance.available_days if balance else 0} days, "
                    f"Requested: {days_to_encash} days."
                )

        return cleaned_data


class LeaveSearchForm(forms.Form):
    """Form for searching leave requests"""
    STATUS_CHOICES = [('', 'All Statuses')] + LeaveRequest.STATUS_CHOICES
    LEAVE_TYPE_CHOICES = [('', 'All Leave Types')]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add leave type choices dynamically
        leave_type_choices = [('', 'All Leave Types')]
        try:
            for leave_type in LeaveType.objects.filter(is_active=True):
                leave_type_choices.append((leave_type.id, leave_type.name))
        except:
            pass  # Handle case when table doesn't exist yet
        
        self.fields['leave_type'].choices = leave_type_choices

    employee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    leave_type = forms.ChoiceField(
        choices=LEAVE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    start_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    submitted_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    submitted_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )


class BulkLeaveBalanceForm(forms.Form):
    """Form for bulk leave balance operations"""
    OPERATION_CHOICES = [
        ('allocate', 'Allocate Leave'),
        ('adjust', 'Adjust Balance'),
        ('carry_forward', 'Carry Forward'),
    ]

    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    leave_type = forms.ModelChoiceField(
        queryset=LeaveType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    year = forms.IntegerField(
        initial=date.today().year,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    days = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'min': '0'
        })
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for bulk operation...'
        })
    ) 