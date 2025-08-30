from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from datetime import datetime, date, timedelta
from .models import SupplierBill
from .forms import SupplierBillForm

def supplier_bill_list(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    
    # Base queryset
    bills = SupplierBill.objects.all()
    
    # Apply filters
    if status_filter:
        bills = bills.filter(status=status_filter)
    
    if supplier_filter:
        bills = bills.filter(supplier__icontains=supplier_filter)
    
    # Order by due date (overdue first, then by due date)
    bills = bills.order_by('due_date')
    
    # Calculate statistics
    total_amount = bills.aggregate(total=Sum('amount'))['total'] or 0
    overdue_amount = bills.filter(
        due_date__lt=date.today(),
        status__in=['draft', 'sent', 'overdue']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Count by status
    status_counts = {}
    for status, label in SupplierBill.STATUS_CHOICES:
        status_counts[status] = bills.filter(status=status).count()
    
    context = {
        'bills': bills,
        'total_amount': total_amount,
        'overdue_amount': overdue_amount,
        'status_counts': status_counts,
        'status_filter': status_filter,
        'supplier_filter': supplier_filter,
        'status_choices': SupplierBill.STATUS_CHOICES,
    }
    
    return render(request, 'supplier_bills/supplier_bill_list.html', context)

def supplier_bill_create(request):
    if request.method == 'POST':
        form = SupplierBillForm(request.POST)
        if form.is_valid():
            supplier_bill = form.save(commit=False)
            supplier = form.cleaned_data['supplier']
            supplier_bill.supplier = supplier.customer_name
            supplier_bill.save()
            messages.success(request, f'Supplier bill {supplier_bill.number} created successfully!')
            return redirect('supplier_bills:detail', pk=supplier_bill.pk)
    else:
        form = SupplierBillForm()
    
    return render(request, 'supplier_bills/supplier_bill_form.html', {'form': form})

def supplier_bill_detail(request, pk):
    supplier_bill = get_object_or_404(SupplierBill, pk=pk)
    return render(request, 'supplier_bills/supplier_bill_detail.html', {
        'supplier_bill': supplier_bill
    })

def supplier_bill_update(request, pk):
    supplier_bill = get_object_or_404(SupplierBill, pk=pk)
    
    if request.method == 'POST':
        form = SupplierBillForm(request.POST, instance=supplier_bill)
        if form.is_valid():
            supplier_bill = form.save(commit=False)
            supplier = form.cleaned_data['supplier']
            supplier_bill.supplier = supplier.customer_name
            supplier_bill.save()
            messages.success(request, f'Supplier bill {supplier_bill.number} updated successfully!')
            return redirect('supplier_bills:detail', pk=supplier_bill.pk)
    else:
        form = SupplierBillForm(instance=supplier_bill)
    
    return render(request, 'supplier_bills/supplier_bill_form.html', {
        'form': form,
        'supplier_bill': supplier_bill,
        'is_update': True
    })

def supplier_bill_delete(request, pk):
    supplier_bill = get_object_or_404(SupplierBill, pk=pk)
    
    if request.method == 'POST':
        number = supplier_bill.number
        supplier_bill.delete()
        messages.success(request, f'Supplier bill {number} deleted successfully!')
        return redirect('supplier_bills:list')
    
    return render(request, 'supplier_bills/supplier_bill_confirm_delete.html', {
        'supplier_bill': supplier_bill
    })

def supplier_bill_print(request, pk):
    supplier_bill = get_object_or_404(SupplierBill, pk=pk)
    
    try:
        from company.company_model import Company
        company = Company.objects.first()
    except:
        company = None
    
    context = {
        'supplier_bill': supplier_bill,
        'company': company,
    }
    
    html_string = render_to_string('supplier_bills/supplier_bill_print.html', context)
    font_config = FontConfiguration()
    html_doc = HTML(string=html_string)
    pdf = html_doc.write_pdf(font_config=font_config)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="supplier_bill_{supplier_bill.number}.pdf"'
    
    return response

def supplier_bill_email(request, pk):
    supplier_bill = get_object_or_404(SupplierBill, pk=pk)
    messages.success(request, f'Supplier bill {supplier_bill.number} sent successfully!')
    return redirect('supplier_bills:detail', pk=supplier_bill.pk)

@require_http_methods(["POST"])
def update_bill_status(request, pk):
    supplier_bill = get_object_or_404(SupplierBill, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(SupplierBill.STATUS_CHOICES):
        supplier_bill.status = new_status
        supplier_bill.save()
        messages.success(request, f'Status updated to {supplier_bill.get_status_display()}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('supplier_bills:detail', pk=supplier_bill.pk)

def supplier_bill_dashboard(request):
    """Dashboard view for supplier bills with statistics"""
    today = date.today()
    
    # Get bills due in next 30 days
    upcoming_due = SupplierBill.objects.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=30),
        status__in=['draft', 'sent', 'overdue']
    ).order_by('due_date')
    
    # Get overdue bills
    overdue_bills = SupplierBill.objects.filter(
        due_date__lt=today,
        status__in=['draft', 'sent', 'overdue']
    ).order_by('due_date')
    
    # Calculate statistics
    total_bills = SupplierBill.objects.count()
    total_amount = SupplierBill.objects.aggregate(total=Sum('amount'))['total'] or 0
    overdue_amount = overdue_bills.aggregate(total=Sum('amount'))['total'] or 0
    upcoming_amount = upcoming_due.aggregate(total=Sum('amount'))['total'] or 0
    
    # Status breakdown
    status_breakdown = {}
    for status, label in SupplierBill.STATUS_CHOICES:
        status_breakdown[status] = SupplierBill.objects.filter(status=status).count()
    
    context = {
        'upcoming_due': upcoming_due,
        'overdue_bills': overdue_bills,
        'total_bills': total_bills,
        'total_amount': total_amount,
        'overdue_amount': overdue_amount,
        'upcoming_amount': upcoming_amount,
        'status_breakdown': status_breakdown,
    }
    
    return render(request, 'supplier_bills/supplier_bill_dashboard.html', context) 