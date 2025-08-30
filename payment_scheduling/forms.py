from django import forms
from django.forms import ModelForm, inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.apps import apps

# Get models dynamically to avoid circular imports
def get_customer_model():
    return apps.get_model('customer', 'Customer')

class PaymentScheduleForm(ModelForm):
    """Form for creating and editing payment schedules"""
    
    class Meta:
        model = apps.get_model('payment_scheduling', 'PaymentSchedule')
        fields = [
            'customer', 'vendor', 'payment_type', 'total_amount', 'currency',
            'vat_rate', 'due_date', 'installment_count', 'installment_amount',
            'invoice_reference', 'po_reference', 'description'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'installment_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'installment_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'invoice_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'po_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for customer field dynamically
        try:
            Customer = get_customer_model()
            self.fields['customer'].queryset = Customer.objects.all()
        except:
            self.fields['customer'].queryset = apps.get_model('customer', 'Customer').objects.none()
        
        # Make fields conditional based on payment type
        if self.instance and self.instance.pk:
            if self.instance.payment_type == 'customer':
                self.fields['vendor'].widget = forms.HiddenInput()
            else:
                self.fields['customer'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        customer = cleaned_data.get('customer')
        vendor = cleaned_data.get('vendor')
        total_amount = cleaned_data.get('total_amount')
        installment_count = cleaned_data.get('installment_count')
        installment_amount = cleaned_data.get('installment_amount')

        # Validate customer/vendor selection based on payment type
        if payment_type == 'customer' and not customer:
            raise ValidationError('Customer is required for customer payments.')
        elif payment_type == 'vendor' and not vendor:
            raise ValidationError('Vendor is required for vendor payments.')

        # Validate amounts
        if total_amount and total_amount <= 0:
            raise ValidationError('Total amount must be greater than zero.')

        if installment_count and installment_count <= 0:
            raise ValidationError('Installment count must be greater than zero.')

        # Calculate and validate installment amount
        if total_amount and installment_count:
            calculated_installment = total_amount / Decimal(installment_count)
            if installment_amount and abs(installment_amount - calculated_installment) > Decimal('0.01'):
                self.add_warning('installment_amount', 
                               f'Installment amount should be approximately {calculated_installment:.2f}')

        return cleaned_data


class PaymentInstallmentForm(ModelForm):
    """Form for individual payment installments"""
    
    class Meta:
        model = apps.get_model('payment_scheduling', 'PaymentInstallment')
        fields = ['installment_number', 'amount', 'due_date', 'status', 'paid_amount', 'paid_date']
        widgets = {
            'installment_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        paid_amount = cleaned_data.get('paid_amount')
        
        if amount and amount <= 0:
            raise ValidationError('Amount must be greater than zero.')
        
        if paid_amount and paid_amount > amount:
            raise ValidationError('Paid amount cannot exceed the installment amount.')
        
        return cleaned_data


class PaymentReminderForm(ModelForm):
    """Form for payment reminders"""
    
    class Meta:
        model = apps.get_model('payment_scheduling', 'PaymentReminder')
        fields = ['reminder_type', 'scheduled_date', 'recipient', 'subject', 'message']
        widgets = {
            'reminder_type': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'recipient': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data['scheduled_date']
        if scheduled_date and scheduled_date < timezone.now():
            raise ValidationError('Scheduled date cannot be in the past.')
        return scheduled_date


class PaymentScheduleFilterForm(forms.Form):
    """Form for filtering payment schedules"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        PaymentSchedule = apps.get_model('payment_scheduling', 'PaymentSchedule')
        
        STATUS_CHOICES = [('', 'All Statuses')] + PaymentSchedule.STATUS_CHOICES
        PAYMENT_TYPE_CHOICES = [('', 'All Types')] + PaymentSchedule.PAYMENT_TYPE_CHOICES
        CURRENCY_CHOICES = [('', 'All Currencies')] + PaymentSchedule.CURRENCY_CHOICES
        
        self.fields['search'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search schedules...'})
        )
        self.fields['status'] = forms.ChoiceField(
            choices=STATUS_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['payment_type'] = forms.ChoiceField(
            choices=PAYMENT_TYPE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['currency'] = forms.ChoiceField(
            choices=CURRENCY_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['date_from'] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        )
        self.fields['date_to'] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        )
        self.fields['overdue_only'] = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
        )


class PaymentScheduleBulkUpdateForm(forms.Form):
    """Form for bulk updating payment schedules"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        PaymentSchedule = apps.get_model('payment_scheduling', 'PaymentSchedule')
        
        ACTION_CHOICES = [
            ('status', 'Change Status'),
            ('add_reminder', 'Add Reminder'),
            ('export', 'Export Selected'),
            ('delete', 'Delete Selected'),
        ]
        
        self.fields['action'] = forms.ChoiceField(
            choices=ACTION_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['new_status'] = forms.ChoiceField(
            choices=PaymentSchedule.STATUS_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['schedule_ids'] = forms.CharField(
            widget=forms.HiddenInput()
        )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        new_status = cleaned_data.get('new_status')
        
        if action == 'status' and not new_status:
            raise ValidationError('New status is required when changing status.')
        
        return cleaned_data


class VATConfigurationForm(ModelForm):
    """Form for VAT configuration"""
    
    class Meta:
        model = apps.get_model('payment_scheduling', 'VATConfiguration')
        fields = ['name', 'vat_rate', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentMethodForm(ModelForm):
    """Form for payment methods"""
    
    class Meta:
        model = apps.get_model('payment_scheduling', 'PaymentMethod')
        fields = ['name', 'code', 'payment_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Inline formsets
PaymentInstallmentFormSet = inlineformset_factory(
    apps.get_model('payment_scheduling', 'PaymentSchedule'),
    apps.get_model('payment_scheduling', 'PaymentInstallment'),
    form=PaymentInstallmentForm,
    extra=1,
    can_delete=True,
    fields=['installment_number', 'amount', 'due_date', 'status', 'paid_amount', 'paid_date']
)


PaymentReminderFormSet = inlineformset_factory(
    apps.get_model('payment_scheduling', 'PaymentSchedule'),
    apps.get_model('payment_scheduling', 'PaymentReminder'),
    form=PaymentReminderForm,
    extra=1,
    can_delete=True,
    fields=['reminder_type', 'scheduled_date', 'recipient', 'subject', 'message']
)
