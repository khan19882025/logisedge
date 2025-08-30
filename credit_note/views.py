from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from .models import CreditNote
from .forms import CreditNoteForm
from invoice.models import Invoice
from customer.models import Customer

def credit_note_list(request):
    notes = CreditNote.objects.all().order_by('-date')
    total_amount = notes.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'credit_note/credit_note_list.html', {
        'notes': notes,
        'total_amount': total_amount
    })

def credit_note_create(request):
    if request.method == 'POST':
        form = CreditNoteForm(request.POST)
        if form.is_valid():
            credit_note = form.save(commit=False)
            # Get the customer object
            customer = form.cleaned_data['customer']
            credit_note.customer = customer.customer_name
            credit_note.save()
            messages.success(request, f'Credit note {credit_note.number} created successfully!')
            return redirect('credit_note:detail', pk=credit_note.pk)
    else:
        form = CreditNoteForm()
    return render(request, 'credit_note/credit_note_form.html', {'form': form})

def credit_note_detail(request, pk):
    """Display credit note details"""
    credit_note = get_object_or_404(CreditNote, pk=pk)
    return render(request, 'credit_note/credit_note_detail.html', {
        'credit_note': credit_note
    })

def credit_note_delete(request, pk):
    """Delete a credit note"""
    credit_note = get_object_or_404(CreditNote, pk=pk)
    
    if request.method == 'POST':
        number = credit_note.number
        credit_note.delete()
        messages.success(request, f'Credit note {number} deleted successfully!')
        return redirect('credit_note:list')
    
    return render(request, 'credit_note/credit_note_confirm_delete.html', {
        'credit_note': credit_note
    })

def credit_note_print(request, pk):
    """Generate PDF for credit note"""
    credit_note = get_object_or_404(CreditNote, pk=pk)
    
    # Get company details for the receipt
    try:
        from company.company_model import Company
        company = Company.objects.first()
    except:
        company = None
    
    context = {
        'credit_note': credit_note,
        'company': company,
    }
    
    # Render the HTML template
    html_string = render_to_string('credit_note/credit_note_print.html', context)
    
    # Configure fonts
    font_config = FontConfiguration()
    
    # Generate PDF
    html_doc = HTML(string=html_string)
    pdf = html_doc.write_pdf(font_config=font_config)
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="credit_note_{credit_note.number}.pdf"'
    
    return response

def credit_note_email(request, pk):
    """Send credit note via email"""
    credit_note = get_object_or_404(CreditNote, pk=pk)
    
    # This would typically send an email with the credit note
    # For now, just return a success message
    messages.success(request, f'Credit note {credit_note.number} sent successfully!')
    
    return redirect('credit_note:detail', pk=credit_note.pk)

@require_http_methods(["GET"])
def get_unpaid_invoices(request):
    """AJAX view to get unpaid invoices for a customer"""
    customer_id = request.GET.get('customer_id')
    
    if not customer_id:
        return JsonResponse({'invoices': []})
    
    try:
        customer = Customer.objects.get(id=customer_id)
        unpaid_statuses = ['draft', 'sent', 'overdue']
        
        invoices = Invoice.objects.filter(
            customer=customer,
            status__in=unpaid_statuses
        ).order_by('-invoice_date')
        
        invoice_data = []
        for invoice in invoices:
            invoice_data.append({
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d'),
                'total_sale': str(invoice.total_sale),
                'status': invoice.get_status_display(),
                'bl_number': invoice.bl_number or '-',
                'items_count': invoice.get_invoice_items_count()
            })
        
        return JsonResponse({
            'success': True,
            'invoices': invoice_data
        })
        
    except Customer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Customer not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 