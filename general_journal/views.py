from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal

from .models import JournalEntry, JournalEntryLine
from .forms import CustomJournalEntryForm, JournalEntrySearchForm
from company.company_model import Company
from fiscal_year.models import FiscalYear
from chart_of_accounts.models import ChartOfAccount


@login_required
def journal_list(request):
    """List all journal entries with search and filtering"""
    
    # Get active company and fiscal year
    try:
        company = Company.objects.get(is_active=True)
        fiscal_year = FiscalYear.objects.get(is_current=True)
    except (Company.DoesNotExist, FiscalYear.DoesNotExist):
        messages.error(request, "Please set up an active company and current fiscal year first.")
        return redirect('dashboard')
    
    # Initialize search form
    search_form = JournalEntrySearchForm(request.GET, company=company)
    
    # Get queryset
    queryset = JournalEntry.objects.filter(
        company=company,
        fiscal_year=fiscal_year
    ).select_related('created_by', 'posted_by').prefetch_related('lines__account__account_type')
    
    # Apply search filters
    if search_form.is_valid():
        search_type = search_form.cleaned_data.get('search_type')
        search_query = search_form.cleaned_data.get('search_query')
        status = search_form.cleaned_data.get('status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        account = search_form.cleaned_data.get('account')
        
        if search_query:
            if search_type == 'journal_number':
                queryset = queryset.filter(journal_number__icontains=search_query)
            elif search_type == 'reference':
                queryset = queryset.filter(reference__icontains=search_query)
            elif search_type == 'description':
                queryset = queryset.filter(description__icontains=search_query)
            elif search_type == 'account':
                queryset = queryset.filter(lines__account__name__icontains=search_query)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        if account:
            queryset = queryset.filter(lines__account=account)
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'company': company,
        'fiscal_year': fiscal_year,
    }
    
    return render(request, 'general_journal/journal_list.html', context)


@login_required
def journal_create(request):
    """Create a new journal entry"""
    
    # Get active company and fiscal year
    try:
        company = Company.objects.get(is_active=True)
        fiscal_year = FiscalYear.objects.get(is_current=True)
    except (Company.DoesNotExist, FiscalYear.DoesNotExist):
        messages.error(request, "Please set up an active company and current fiscal year first.")
        return redirect('dashboard')
    
    # Get accounts for dropdown
    accounts = ChartOfAccount.objects.filter(
        company=company,
        is_active=True,
        is_group=False
    ).select_related('account_type').order_by('account_type__name', 'name')
    
    if request.method == 'POST':
        print("POST request received")
        form = CustomJournalEntryForm(request.POST, user=request.user)
        
        # Debug: Print form details
        print("Form class:", type(form))
        print("Form fields:", list(form.fields.keys()))
        print("Form is valid:", form.is_valid())
        
        if not form.is_valid():
            print("Form errors:", form.errors)
            print("Form non-field errors:", form.non_field_errors())
            print("Form data:", request.POST)
        
        if form.is_valid():
            try:
                print("Form is valid, creating journal entry...")
                # Create journal entry using the custom form save method
                journal_entry = form.save(company, fiscal_year, request.user)
                print("Journal entry created:", journal_entry)
                
                # Process journal lines from form data
                line_count = 1
                while f'account_{line_count}' in request.POST:
                    account_id = request.POST.get(f'account_{line_count}')
                    debit_amount = request.POST.get(f'debit_{line_count}', '0')
                    credit_amount = request.POST.get(f'credit_{line_count}', '0')
                    
                    if account_id and (debit_amount != '0' or credit_amount != '0'):
                        try:
                            account = ChartOfAccount.objects.get(id=account_id)
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=account,
                                debit_amount=Decimal(debit_amount) if debit_amount else 0,
                                credit_amount=Decimal(credit_amount) if credit_amount else 0
                            )
                        except ChartOfAccount.DoesNotExist:
                            pass
                    
                    line_count += 1
                
                # Calculate totals
                journal_entry.calculate_totals()
                
                messages.success(request, f"Journal entry {journal_entry.journal_number} created successfully.")
                return redirect('general_journal:journal_detail', pk=journal_entry.pk)
                
            except Exception as e:
                # If there's an error, add it to form errors
                form.add_error(None, f"Error creating journal entry: {str(e)}")
                print("Exception occurred:", str(e))
                import traceback
                traceback.print_exc()
    else:
        form = CustomJournalEntryForm(user=request.user, initial={'date': timezone.now().date()})
    
    context = {
        'form': form,
        'accounts': accounts,
        'company': company,
        'fiscal_year': fiscal_year,
    }
    
    return render(request, 'general_journal/journal_form.html', context)


@login_required
def journal_update(request, pk):
    """Update an existing journal entry"""
    
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    # Check if journal entry can be edited
    if journal_entry.status != 'draft':
        messages.error(request, "Only draft journal entries can be edited.")
        return redirect('general_journal:journal_detail', pk=pk)
    
    # Get accounts for dropdown
    accounts = ChartOfAccount.objects.filter(
        company=journal_entry.company,
        is_active=True,
        is_group=False
    ).select_related('account_type').order_by('account_type__name', 'name')
    
    if request.method == 'POST':
        form = CustomJournalEntryForm(request.POST, instance=journal_entry, user=request.user)
        
        if form.is_valid():
            try:
                # Update journal entry using the custom form save method
                journal_entry = form.save(journal_entry.company, journal_entry.fiscal_year, request.user)
                
                # Clear existing lines
                journal_entry.lines.all().delete()
                
                # Process journal lines from form data
                line_count = 1
                while f'account_{line_count}' in request.POST:
                    account_id = request.POST.get(f'account_{line_count}')
                    debit_amount = request.POST.get(f'debit_{line_count}', '0')
                    credit_amount = request.POST.get(f'credit_{line_count}', '0')
                    
                    if account_id and (debit_amount != '0' or credit_amount != '0'):
                        try:
                            account = ChartOfAccount.objects.get(id=account_id)
                            JournalEntryLine.objects.create(
                                journal_entry=journal_entry,
                                account=account,
                                debit_amount=Decimal(debit_amount) if debit_amount else 0,
                                credit_amount=Decimal(credit_amount) if credit_amount else 0
                            )
                        except ChartOfAccount.DoesNotExist:
                            pass
                    
                    line_count += 1
                
                # Calculate totals
                journal_entry.calculate_totals()
                
                messages.success(request, f"Journal entry {journal_entry.journal_number} updated successfully.")
                return redirect('general_journal:journal_detail', pk=journal_entry.pk)
                
            except Exception as e:
                # If there's an error, add it to form errors
                form.add_error(None, f"Error updating journal entry: {str(e)}")
    else:
        form = CustomJournalEntryForm(instance=journal_entry, user=request.user)
    
    context = {
        'form': form,
        'journal_entry': journal_entry,
        'accounts': accounts,
        'company': journal_entry.company,
        'fiscal_year': journal_entry.fiscal_year,
    }
    
    return render(request, 'general_journal/journal_form.html', context)


@login_required
def journal_detail(request, pk):
    """View journal entry details"""
    
    journal_entry = get_object_or_404(
        JournalEntry.objects.select_related('company', 'fiscal_year', 'created_by', 'posted_by')
        .prefetch_related('lines__account__account_type'),
        pk=pk
    )
    
    context = {
        'journal_entry': journal_entry,
        'company': journal_entry.company,
        'fiscal_year': journal_entry.fiscal_year,
    }
    
    return render(request, 'general_journal/journal_detail.html', context)


@login_required
def journal_delete(request, pk):
    """Delete a journal entry"""
    
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == 'POST':
        if journal_entry.status != 'draft':
            messages.error(request, "Only draft journal entries can be deleted.")
        else:
            journal_number = journal_entry.journal_number
            journal_entry.delete()
            messages.success(request, f"Journal entry {journal_number} deleted successfully.")
        
        return redirect('general_journal:journal_list')
    
    context = {
        'journal_entry': journal_entry,
        'company': journal_entry.company,
        'fiscal_year': journal_entry.fiscal_year,
    }
    
    return render(request, 'general_journal/journal_confirm_delete.html', context)


@login_required
def journal_post(request, pk):
    """Post a journal entry"""
    
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == 'POST':
        if journal_entry.post(request.user):
            messages.success(request, f"Journal entry {journal_entry.journal_number} posted successfully.")
        else:
            messages.error(request, "Journal entry cannot be posted. Please ensure it is balanced and has at least 2 lines.")
        
        return redirect('general_journal:journal_detail', pk=pk)
    
    context = {
        'journal_entry': journal_entry,
        'company': journal_entry.company,
        'fiscal_year': journal_entry.fiscal_year,
    }
    
    return render(request, 'general_journal/journal_confirm_post.html', context)


@login_required
def journal_cancel(request, pk):
    """Cancel a journal entry"""
    
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == 'POST':
        if journal_entry.cancel():
            messages.success(request, f"Journal entry {journal_entry.journal_number} cancelled successfully.")
        else:
            messages.error(request, "Only draft journal entries can be cancelled.")
        
        return redirect('general_journal:journal_detail', pk=pk)
    
    context = {
        'journal_entry': journal_entry,
        'company': journal_entry.company,
        'fiscal_year': journal_entry.fiscal_year,
    }
    
    return render(request, 'general_journal/journal_confirm_cancel.html', context)


@login_required
def journal_print(request, pk):
    """Print view for journal entry"""
    
    journal_entry = get_object_or_404(
        JournalEntry.objects.select_related('company', 'fiscal_year', 'created_by', 'posted_by')
        .prefetch_related('lines__account__account_type'),
        pk=pk
    )
    
    context = {
        'journal_entry': journal_entry,
        'company': journal_entry.company,
        'fiscal_year': journal_entry.fiscal_year,
        'print_date': timezone.now(),
    }
    
    return render(request, 'general_journal/journal_print.html', context)
