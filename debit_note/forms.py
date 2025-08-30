from django import forms
from django.db.models import Q
from datetime import date
from .models import DebitNote
from invoice.models import Invoice
from customer.models import Customer

class DebitNoteForm(forms.ModelForm):
    supplier = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'supplier-select'
        }),
        label='Supplier *'
    )
    
    selected_invoices = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'selected-invoices'
        })
    )
    
    class Meta:
        model = DebitNote
        fields = ['number', 'date', 'supplier', 'amount']
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
        if not self.instance.pk:  # Only for new debit notes
            self.fields['date'].initial = date.today()
        
        # Get suppliers with unpaid invoices using reverse relationship
        unpaid_statuses = ['draft', 'sent', 'overdue']
        suppliers_with_unpaid = Customer.objects.filter(
            customer_types__name__icontains='supplier',
            invoice__status__in=unpaid_statuses
        ).distinct().order_by('customer_name')
        
        # Create choices for supplier dropdown
        supplier_choices = [('', 'Select a supplier')]
        for supplier in suppliers_with_unpaid:
            supplier_choices.append((supplier.id, supplier.customer_name))
        
        self.fields['supplier'].choices = supplier_choices
    
    def clean_supplier(self):
        supplier_id = self.cleaned_data.get('supplier')
        if supplier_id:
            try:
                return Customer.objects.get(id=supplier_id)
            except Customer.DoesNotExist:
                raise forms.ValidationError("Selected supplier does not exist.")
        return None 