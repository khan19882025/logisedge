from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from .models import DebitNote
from .forms import DebitNoteForm
from invoice.models import Invoice
from customer.models import Customer

def debit_note_list(request):
    notes = DebitNote.objects.all().order_by('-date')
    total_amount = notes.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'debit_note/debit_note_list.html', {
        'notes': notes,
        'total_amount': total_amount
    })

def debit_note_create(request):
    if request.method == 'POST':
        form = DebitNoteForm(request.POST)
        if form.is_valid():
            debit_note = form.save(commit=False)
            supplier = form.cleaned_data['supplier']
            debit_note.supplier = supplier.customer_name
            debit_note.save()
            messages.success(request, f'Debit note {debit_note.number} created successfully!')
            return redirect('debit_note:detail', pk=debit_note.pk)
    else:
        form = DebitNoteForm()
    return render(request, 'debit_note/debit_note_form.html', {'form': form})

def debit_note_detail(request, pk):
    debit_note = get_object_or_404(DebitNote, pk=pk)
    return render(request, 'debit_note/debit_note_detail.html', {
        'debit_note': debit_note
    })

def debit_note_delete(request, pk):
    debit_note = get_object_or_404(DebitNote, pk=pk)
    
    if request.method == 'POST':
        number = debit_note.number
        debit_note.delete()
        messages.success(request, f'Debit note {number} deleted successfully!')
        return redirect('debit_note:list')
    
    return render(request, 'debit_note/debit_note_confirm_delete.html', {
        'debit_note': debit_note
    })

def debit_note_print(request, pk):
    debit_note = get_object_or_404(DebitNote, pk=pk)
    
    try:
        from company.company_model import Company
        company = Company.objects.first()
    except:
        company = None
    
    context = {
        'debit_note': debit_note,
        'company': company,
    }
    
    html_string = render_to_string('debit_note/debit_note_print.html', context)
    font_config = FontConfiguration()
    html_doc = HTML(string=html_string)
    pdf = html_doc.write_pdf(font_config=font_config)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="debit_note_{debit_note.number}.pdf"'
    
    return response

def debit_note_email(request, pk):
    debit_note = get_object_or_404(DebitNote, pk=pk)
    messages.success(request, f'Debit note {debit_note.number} sent successfully!')
    return redirect('debit_note:detail', pk=debit_note.pk)

@require_http_methods(["GET"])
def get_unpaid_invoices(request):
    supplier_id = request.GET.get('supplier_id')
    
    if not supplier_id:
        return JsonResponse({'invoices': []})
    
    try:
        supplier = Customer.objects.get(id=supplier_id)
        unpaid_statuses = ['draft', 'sent', 'overdue']
        
        invoices = Invoice.objects.filter(
            customer=supplier,
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
            'error': 'Supplier not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 