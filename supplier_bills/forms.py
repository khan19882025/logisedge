from django import forms
from datetime import date, timedelta
from .models import SupplierBill
from customer.models import Customer

class SupplierBillForm(forms.ModelForm):
    supplier = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'supplier-select'
        }),
        label='Supplier *'
    )
    
    class Meta:
        model = SupplierBill
        fields = ['number', 'supplier', 'bill_date', 'due_date', 'amount', 'status', 'reference_number', 'notes']
        widgets = {
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated after save'
            }),
            'bill_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Enter additional notes'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set current date as default for new bills
        if not self.instance.pk:  # Only for new supplier bills
            self.fields['bill_date'].initial = date.today()
            self.fields['due_date'].initial = date.today() + timedelta(days=30)
        
        # Get suppliers (customers with supplier type)
        suppliers = Customer.objects.filter(
            customer_types__name__icontains='supplier'
        ).distinct().order_by('customer_name')
        
        # Create choices for supplier dropdown
        supplier_choices = [('', 'Select a supplier')]
        for supplier in suppliers:
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
    
    def clean(self):
        cleaned_data = super().clean()
        bill_date = cleaned_data.get('bill_date')
        due_date = cleaned_data.get('due_date')
        
        if bill_date and due_date and due_date < bill_date:
            raise forms.ValidationError("Due date cannot be earlier than bill date.")
        
        return cleaned_data 