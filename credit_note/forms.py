from django import forms
from django.db.models import Q
from datetime import date
from .models import CreditNote
from invoice.models import Invoice
from customer.models import Customer

class CreditNoteForm(forms.ModelForm):
    customer = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'customer-select'
        }),
        label='Customer *'
    )
    
    selected_invoices = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'selected-invoices'
        })
    )
    
    class Meta:
        model = CreditNote
        fields = ['number', 'date', 'customer', 'amount']
        widgets = {
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated after save'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set current date as default
        if not self.instance.pk:  # Only for new credit notes
            self.fields['date'].initial = date.today()
        
        # Get customers with unpaid invoices using reverse relationship
        unpaid_statuses = ['draft', 'sent', 'overdue']
        customers_with_unpaid = Customer.objects.filter(
            invoice__status__in=unpaid_statuses
        ).distinct().order_by('customer_name')
        
        # Create choices for customer dropdown
        customer_choices = [('', 'Select a customer')]
        for customer in customers_with_unpaid:
            customer_choices.append((customer.id, customer.customer_name))
        
        self.fields['customer'].choices = customer_choices
    
    def clean_customer(self):
        customer_id = self.cleaned_data.get('customer')
        if customer_id:
            try:
                return Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                raise forms.ValidationError("Selected customer does not exist.")
        return None 