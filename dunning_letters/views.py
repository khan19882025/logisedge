from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from datetime import datetime, timedelta, date
from .models import DunningLetter
from .forms import DunningLetterForm, DunningLetterFilterForm

def get_customers_with_unpaid_invoices():
    """Get customers who have unpaid invoices"""
    try:
        from invoice.models import Invoice
        from customer.models import Customer
        
        # Get customers with overdue invoices
        overdue_customers = Customer.objects.filter(
            invoice__due_date__lt=date.today(),
            invoice__status__in=['sent', 'overdue']
        ).distinct().order_by('customer_name')
        
        return [(customer.id, customer.customer_name) for customer in overdue_customers]
    except:
        return []

def dunning_letter_list(request):
    """List all dunning letters with filtering and statistics"""
    # Get filter parameters
    form = DunningLetterFilterForm(request.GET)
    
    # Populate customer choices
    customer_choices = [('', 'All Customers')] + get_customers_with_unpaid_invoices()
    form.fields['customer'].choices = customer_choices
    
    letters = DunningLetter.objects.all()
    
    if form.is_valid():
        customer = form.cleaned_data.get('customer')
        level = form.cleaned_data.get('level')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        overdue_days_min = form.cleaned_data.get('overdue_days_min')
        overdue_days_max = form.cleaned_data.get('overdue_days_max')
        
        # Apply filters
        if customer:
            letters = letters.filter(customer_id=customer)
        if level:
            letters = letters.filter(level=level)
        if status:
            letters = letters.filter(status=status)
        if date_from:
            letters = letters.filter(created_at__date__gte=date_from)
        if date_to:
            letters = letters.filter(created_at__date__lte=date_to)
        if overdue_days_min is not None:
            letters = letters.filter(overdue_days__gte=overdue_days_min)
        if overdue_days_max is not None:
            letters = letters.filter(overdue_days__lte=overdue_days_max)
    
    # Calculate statistics
    total_letters = letters.count()
    total_overdue_amount = letters.aggregate(total=Sum('overdue_amount'))['total'] or 0
    
    # Count by level
    level_counts = {}
    for level, label in DunningLetter.LEVEL_CHOICES:
        level_counts[level] = letters.filter(level=level).count()
    
    # Count by status
    status_counts = {}
    for status, label in DunningLetter.STATUS_CHOICES:
        status_counts[status] = letters.filter(status=status).count()
    
    # Recent activity
    recent_letters = letters.order_by('-created_at')[:5]
    
    context = {
        'letters': letters,
        'form': form,
        'total_letters': total_letters,
        'total_overdue_amount': total_overdue_amount,
        'level_counts': level_counts,
        'status_counts': status_counts,
        'recent_letters': recent_letters,
        'level_choices': DunningLetter.LEVEL_CHOICES,
        'status_choices': DunningLetter.STATUS_CHOICES,
    }
    
    return render(request, 'dunning_letters/dunning_letter_list.html', context)

def dunning_letter_detail(request, pk):
    """Show detailed view of a dunning letter"""
    letter = get_object_or_404(DunningLetter, pk=pk)
    
    # Mark as viewed if status is sent
    if letter.status == 'sent':
        letter.mark_as_viewed()
    
    context = {
        'letter': letter,
    }
    
    return render(request, 'dunning_letters/dunning_letter_detail.html', context)

def dunning_letter_create(request):
    """Create a new dunning letter"""
    if request.method == 'POST':
        form = DunningLetterForm(request.POST)
        
        # Populate customer choices
        customer_choices = [('', 'Select Customer')] + get_customers_with_unpaid_invoices()
        form.fields['customer'].choices = customer_choices
        
        if form.is_valid():
            letter = form.save(commit=False)
            
            # Set customer from form
            customer_id = form.cleaned_data['customer']
            if customer_id:
                try:
                    from customer.models import Customer
                    customer = Customer.objects.get(pk=customer_id)
                    letter.customer = customer
                    
                    # Get the most overdue invoice for this customer
                    from invoice.models import Invoice
                    overdue_invoice = Invoice.objects.filter(
                        customer=customer,
                        due_date__lt=date.today(),
                        status__in=['sent', 'overdue']
                    ).order_by('due_date').first()
                    
                    if overdue_invoice:
                        letter.invoice = overdue_invoice
                        letter.overdue_amount = overdue_invoice.total_amount
                        letter.overdue_days = (date.today() - overdue_invoice.due_date).days
                        letter.due_date = overdue_invoice.due_date
                    
                    letter.save()
                    messages.success(request, f'Dunning letter created successfully!')
                    return redirect('dunning_letters:detail', pk=letter.pk)
                    
                except Customer.DoesNotExist:
                    messages.error(request, 'Invalid customer selected.')
            else:
                messages.error(request, 'Please select a customer.')
    else:
        form = DunningLetterForm()
        # Populate customer choices
        customer_choices = [('', 'Select Customer')] + get_customers_with_unpaid_invoices()
        form.fields['customer'].choices = customer_choices
    
    context = {
        'form': form,
    }
    
    return render(request, 'dunning_letters/dunning_letter_form.html', context)

def dunning_letter_update(request, pk):
    """Update an existing dunning letter"""
    letter = get_object_or_404(DunningLetter, pk=pk)
    
    if request.method == 'POST':
        form = DunningLetterForm(request.POST, instance=letter)
        if form.is_valid():
            letter = form.save()
            messages.success(request, f'Dunning letter updated successfully!')
            return redirect('dunning_letters:detail', pk=letter.pk)
    else:
        form = DunningLetterForm(instance=letter)
    
    context = {
        'form': form,
        'letter': letter,
        'is_update': True,
    }
    
    return render(request, 'dunning_letters/dunning_letter_form.html', context)

def dunning_letter_delete(request, pk):
    """Delete a dunning letter"""
    letter = get_object_or_404(DunningLetter, pk=pk)
    
    if request.method == 'POST':
        letter.delete()
        messages.success(request, 'Dunning letter deleted successfully!')
        return redirect('dunning_letters:list')
    
    return render(request, 'dunning_letters/dunning_letter_confirm_delete.html', {
        'letter': letter
    })

def dunning_letter_send_email(request, pk):
    """Send dunning letter via email"""
    letter = get_object_or_404(DunningLetter, pk=pk)
    
    if request.method == 'POST':
        email_recipient = request.POST.get('email_recipient', letter.customer.email)
        
        if email_recipient:
            try:
                # Send email
                send_mail(
                    subject=letter.subject,
                    message=letter.content,
                    from_email='noreply@logisedge.com',
                    recipient_list=[email_recipient],
                    fail_silently=False,
                )
                
                # Mark as sent
                letter.mark_as_sent(email_recipient)
                messages.success(request, f'Dunning letter sent successfully to {email_recipient}')
                
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
        else:
            messages.error(request, 'No email address provided.')
    
    return redirect('dunning_letters:detail', pk=letter.pk)

def dunning_letter_print(request, pk):
    """Generate PDF of dunning letter"""
    letter = get_object_or_404(DunningLetter, pk=pk)
    
    try:
        from company.company_model import Company
        company = Company.objects.first()
    except:
        company = None
    
    context = {
        'letter': letter,
        'company': company,
    }
    
    html_string = render_to_string('dunning_letters/dunning_letter_print.html', context)
    font_config = FontConfiguration()
    html_doc = HTML(string=html_string)
    pdf = html_doc.write_pdf(font_config=font_config)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dunning_letter_{letter.level}_{letter.customer.customer_name}_{letter.invoice.invoice_number}.pdf"'
    
    return response

def dunning_letter_dashboard(request):
    """Dashboard view with statistics and overview"""
    today = date.today()
    
    # Get overdue invoices that need dunning letters
    try:
        from invoice.models import Invoice
        overdue_invoices = Invoice.objects.filter(
            due_date__lt=today,
            status__in=['sent', 'overdue']
        ).select_related('customer')
    except:
        overdue_invoices = []
    
    # Get dunning letters statistics
    total_letters = DunningLetter.objects.count()
    sent_letters = DunningLetter.objects.filter(email_sent=True).count()
    paid_letters = DunningLetter.objects.filter(status='paid').count()
    
    # Calculate total overdue amount
    total_overdue_amount = sum(invoice.total_amount for invoice in overdue_invoices)
    
    # Level breakdown
    level_breakdown = {}
    for level, label in DunningLetter.LEVEL_CHOICES:
        level_breakdown[level] = DunningLetter.objects.filter(level=level).count()
    
    # Status breakdown
    status_breakdown = {}
    for status, label in DunningLetter.STATUS_CHOICES:
        status_breakdown[status] = DunningLetter.objects.filter(status=status).count()
    
    # Recent dunning letters
    recent_letters = DunningLetter.objects.order_by('-created_at')[:10]
    
    # Customers with most overdue invoices
    customer_overdue = {}
    for invoice in overdue_invoices:
        customer_name = invoice.customer.customer_name
        if customer_name not in customer_overdue:
            customer_overdue[customer_name] = {
                'count': 0,
                'amount': 0,
                'customer': invoice.customer
            }
        customer_overdue[customer_name]['count'] += 1
        customer_overdue[customer_name]['amount'] += invoice.total_amount
    
    context = {
        'overdue_invoices': overdue_invoices,
        'total_letters': total_letters,
        'sent_letters': sent_letters,
        'paid_letters': paid_letters,
        'total_overdue_amount': total_overdue_amount,
        'level_breakdown': level_breakdown,
        'status_breakdown': status_breakdown,
        'recent_letters': recent_letters,
        'customer_overdue': customer_overdue,
    }
    
    return render(request, 'dunning_letters/dunning_letter_dashboard.html', context)

@require_http_methods(["POST"])
def update_letter_status(request, pk):
    """Update dunning letter status"""
    letter = get_object_or_404(DunningLetter, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(DunningLetter.STATUS_CHOICES):
        letter.status = new_status
        letter.save()
        messages.success(request, f'Status updated to {letter.get_status_display()}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('dunning_letters:detail', pk=letter.pk)

def get_overdue_invoices(request):
    """AJAX endpoint to get overdue invoices for a customer"""
    customer_id = request.GET.get('customer_id')
    
    if customer_id:
        try:
            from invoice.models import Invoice
            overdue_invoices = Invoice.objects.filter(
                customer_id=customer_id,
                due_date__lt=date.today(),
                status__in=['sent', 'overdue']
            ).values('id', 'invoice_number', 'total_amount', 'due_date', 'status')
            
            return JsonResponse({'invoices': list(overdue_invoices)})
        except:
            pass
    
    return JsonResponse({'invoices': []})
