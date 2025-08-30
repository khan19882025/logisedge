from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import inlineformset_factory
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import weasyprint
from io import BytesIO
from PyPDF2 import PdfMerger
import tempfile
import os

from .models import GRN, GRNItem, GRNPallet
from .forms import GRNForm, GRNItemForm, GRNItemFormSet
from customer.models import Customer
from facility.models import Facility
from items.models import Item
from job.models import Job
from salesman.models import Salesman
from company.company_model import Company


class GRNListView(LoginRequiredMixin, ListView):
    """View for listing all GRNs with search and filtering"""
    model = GRN
    template_name = 'grn/grn_list.html'
    context_object_name = 'grns'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = GRN.objects.all()
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(grn_number__icontains=search_query) |
                Q(customer__customer_name__icontains=search_query) |
                Q(supplier_name__icontains=search_query) |
                Q(container_number__icontains=search_query) |
                Q(bl_number__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority_filter = self.request.GET.get('priority', '')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by facility
        facility_filter = self.request.GET.get('facility', '')
        if facility_filter:
            queryset = queryset.filter(facility_id=facility_filter)
        
        # Sort by
        sort_by = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['priority_filter'] = self.request.GET.get('priority', '')
        context['facility_filter'] = self.request.GET.get('facility', '')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        context['status_choices'] = GRN.GRN_STATUS
        context['priority_choices'] = GRN._meta.get_field('priority').choices
        context['facilities'] = Facility.objects.all()
        return context


class GRNCreateView(LoginRequiredMixin, CreateView):
    """View for creating new GRN"""
    model = GRN
    form_class = GRNForm
    template_name = 'grn/grn_form.html'
    
    def get_success_url(self):
        return reverse_lazy('grn:grn_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        print("=== GRN CREATE FORM_VALID METHOD CALLED ===")
        print("Form is valid:", form.is_valid())
        print("Form errors:", form.errors)
        print("Job ref value:", form.cleaned_data.get('job_ref'))
        print("All form data:", form.cleaned_data)
        
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Process custom table data for GRN items
        self.process_grn_items(form.instance)
        
        messages.success(self.request, f'GRN {form.instance.grn_number} created successfully!')
        return response
    
    def form_invalid(self, form):
        print("=== GRN CREATE FORM_INVALID METHOD CALLED ===")
        print("Form is valid:", form.is_valid())
        print("Form errors:", form.errors)
        print("Job ref value:", form.data.get('job_ref'))
        print("All form data:", form.data)
        return super().form_invalid(form)
    
    def process_grn_items(self, grn_instance):
        """Process GRN items and pallets from custom table data"""
        # Get item data from POST
        item_codes = self.request.POST.getlist('item_code[]')
        item_ids = self.request.POST.getlist('item[]')
        hs_codes = self.request.POST.getlist('hs_code[]')
        coos = self.request.POST.getlist('coo[]')
        units = self.request.POST.getlist('unit[]')
        qtys = self.request.POST.getlist('qty[]')
        g_weights = self.request.POST.getlist('g_weight[]')
        n_weights = self.request.POST.getlist('n_weight[]')
        cbms = self.request.POST.getlist('cbm[]')
        p_dates = self.request.POST.getlist('p_date[]')
        e_dates = self.request.POST.getlist('e_date[]')
        colors = self.request.POST.getlist('color[]')
        sizes = self.request.POST.getlist('size[]')
        barcodes = self.request.POST.getlist('barcode[]')
        eds = self.request.POST.getlist('ed[]')
        ctnrs = self.request.POST.getlist('ctnr[]')
        remarks = self.request.POST.getlist('remark[]')
        
        # Create GRN items
        for i in range(len(item_codes)):
            if item_codes[i] or item_ids[i]:  # Only create if there's data
                try:
                    item = None
                    if item_ids[i]:
                        item = Item.objects.get(id=item_ids[i])
                    
                    # Only create GRNItem if we have either an item or item_code
                    if item or item_codes[i]:
                        GRNItem.objects.create(
                            grn=grn_instance,
                            item=item,
                            item_code=item_codes[i] or '',
                            item_name=item.item_name if item else '',
                            hs_code=hs_codes[i] or '',
                            unit=units[i] or '',
                            expected_qty=float(qtys[i]) if qtys[i] else None,
                            received_qty=float(qtys[i]) if qtys[i] else None,  # Use same as expected for now
                            net_weight=float(n_weights[i]) if n_weights[i] else None,
                            gross_weight=float(g_weights[i]) if g_weights[i] else None,
                            volume=float(cbms[i]) if cbms[i] else None,
                            coo=coos[i] or '',
                            batch_number=barcodes[i] or '',
                            expiry_date=e_dates[i] if e_dates[i] else None,
                            p_date=p_dates[i] if p_dates[i] else None,
                            color=colors[i] or '',
                            size=sizes[i] or '',
                            ed=eds[i] or '',
                            ctnr=ctnrs[i] or '',
                            remark=remarks[i] or ''
                        )
                except (ValueError, Item.DoesNotExist):
                    # Skip invalid items
                    continue
        
        # Process pallet data
        self.process_grn_pallets(grn_instance)
    
    def process_grn_pallets(self, grn_instance):
        """Process GRN pallets from custom table data"""
        # Get pallet data from POST
        pallet_nos = self.request.POST.getlist('pallet_no[]')
        pallet_descriptions = self.request.POST.getlist('pallet_description[]')
        pallet_qtys = self.request.POST.getlist('pallet_qty[]')
        pallet_locations = self.request.POST.getlist('pallet_location[]')
        pallet_remarks = self.request.POST.getlist('pallet_remark[]')
        
        # Create GRN pallets
        for i in range(len(pallet_nos)):
            if pallet_nos[i]:  # Only create if there's a pallet number
                try:
                    GRNPallet.objects.create(
                        grn=grn_instance,
                        pallet_no=pallet_nos[i],
                        description=pallet_descriptions[i] or '',
                        quantity=float(pallet_qtys[i]) if pallet_qtys[i] else 0,
                        location=pallet_locations[i] or '',
                        remark=pallet_remarks[i] or ''
                    )
                except ValueError:
                    # Skip invalid pallets
                    continue
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New GRN'
        context['submit_text'] = 'Create GRN'
        context['customers'] = Customer.objects.all()
        context['facilities'] = Facility.objects.all()
        context['items'] = Item.objects.all()
        context['salesmen'] = Salesman.objects.all().order_by('first_name')
        return context


class GRNUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating existing GRN"""
    model = GRN
    form_class = GRNForm
    template_name = 'grn/grn_form.html'
    success_url = reverse_lazy('grn:grn_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Clear existing items and pallets, then process new ones
        form.instance.items.all().delete()
        form.instance.pallets.all().delete()
        self.process_grn_items(form.instance)
        
        messages.success(self.request, f'GRN {form.instance.grn_number} updated successfully!')
        return response
    
    def process_grn_items(self, grn_instance):
        """Process GRN items and pallets from custom table data"""
        # Get item data from POST
        item_codes = self.request.POST.getlist('item_code[]')
        item_ids = self.request.POST.getlist('item[]')
        hs_codes = self.request.POST.getlist('hs_code[]')
        coos = self.request.POST.getlist('coo[]')
        units = self.request.POST.getlist('unit[]')
        qtys = self.request.POST.getlist('qty[]')
        g_weights = self.request.POST.getlist('g_weight[]')
        n_weights = self.request.POST.getlist('n_weight[]')
        cbms = self.request.POST.getlist('cbm[]')
        p_dates = self.request.POST.getlist('p_date[]')
        e_dates = self.request.POST.getlist('e_date[]')
        colors = self.request.POST.getlist('color[]')
        sizes = self.request.POST.getlist('size[]')
        barcodes = self.request.POST.getlist('barcode[]')
        eds = self.request.POST.getlist('ed[]')
        ctnrs = self.request.POST.getlist('ctnr[]')
        remarks = self.request.POST.getlist('remark[]')
        
        # Create GRN items
        for i in range(len(item_codes)):
            if item_codes[i] or item_ids[i]:  # Only create if there's data
                try:
                    item = None
                    if item_ids[i]:
                        item = Item.objects.get(id=item_ids[i])
                    
                    # Only create GRNItem if we have either an item or item_code
                    if item or item_codes[i]:
                        GRNItem.objects.create(
                            grn=grn_instance,
                            item=item,
                            item_code=item_codes[i] or '',
                            item_name=item.item_name if item else '',
                            hs_code=hs_codes[i] or '',
                            unit=units[i] or '',
                            expected_qty=float(qtys[i]) if qtys[i] else None,
                            received_qty=float(qtys[i]) if qtys[i] else None,  # Use same as expected for now
                            net_weight=float(n_weights[i]) if n_weights[i] else None,
                            gross_weight=float(g_weights[i]) if g_weights[i] else None,
                            volume=float(cbms[i]) if cbms[i] else None,
                            coo=coos[i] or '',
                            batch_number=barcodes[i] or '',
                            expiry_date=e_dates[i] if e_dates[i] else None,
                            p_date=p_dates[i] if p_dates[i] else None,
                            color=colors[i] or '',
                            size=sizes[i] or '',
                            ed=eds[i] or '',
                            ctnr=ctnrs[i] or '',
                            remark=remarks[i] or ''
                        )
                except (ValueError, Item.DoesNotExist):
                    # Skip invalid items
                    continue
        
        # Process pallet data
        self.process_grn_pallets(grn_instance)
    
    def process_grn_pallets(self, grn_instance):
        """Process GRN pallets from custom table data"""
        # Get pallet data from POST
        pallet_nos = self.request.POST.getlist('pallet_no[]')
        pallet_descriptions = self.request.POST.getlist('pallet_description[]')
        pallet_qtys = self.request.POST.getlist('pallet_qty[]')
        pallet_locations = self.request.POST.getlist('pallet_location[]')
        pallet_remarks = self.request.POST.getlist('pallet_remark[]')
        
        # Create GRN pallets
        for i in range(len(pallet_nos)):
            if pallet_nos[i]:  # Only create if there's a pallet number
                try:
                    GRNPallet.objects.create(
                        grn=grn_instance,
                        pallet_no=pallet_nos[i],
                        description=pallet_descriptions[i] or '',
                        quantity=float(pallet_qtys[i]) if pallet_qtys[i] else 0,
                        location=pallet_locations[i] or '',
                        remark=pallet_remarks[i] or ''
                    )
                except ValueError:
                    # Skip invalid pallets
                    continue
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit GRN {self.object.grn_number}'
        context['submit_text'] = 'Update GRN'
        context['customers'] = Customer.objects.all()
        context['facilities'] = Facility.objects.all()
        context['items'] = Item.objects.all()
        context['salesmen'] = Salesman.objects.all().order_by('first_name')
        # Add existing GRN items and pallets for editing
        context['existing_grn_items'] = self.object.items.all()
        context['existing_grn_pallets'] = self.object.pallets.all()
        return context


class GRNDetailView(LoginRequiredMixin, DetailView):
    """View for displaying GRN details"""
    model = GRN
    template_name = 'grn/grn_detail.html'
    context_object_name = 'grn'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grn_items'] = self.object.items.all()
        context['grn_pallets'] = self.object.pallets.all()
        return context


class GRNDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting GRN"""
    model = GRN
    template_name = 'grn/grn_confirm_delete.html'
    success_url = reverse_lazy('grn:grn_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'GRN deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def grn_status_update(request, pk):
    """Update GRN status"""
    grn = get_object_or_404(GRN, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(GRN.GRN_STATUS):
            grn.status = new_status
            if new_status == 'completed':
                grn.received_date = timezone.now().date()
            grn.save()
            messages.success(request, f'GRN status updated to {grn.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('grn:grn_detail', pk=pk)


@login_required
def grn_quick_view(request, pk):
    """Quick view for GRN"""
    grn = get_object_or_404(GRN, pk=pk)
    return render(request, 'grn/grn_quick_view.html', {'grn': grn})


@login_required
def grn_duplicate(request, pk):
    """Duplicate GRN"""
    original_grn = get_object_or_404(GRN, pk=pk)
    
    # Create a new GRN with copied data
    new_grn = GRN.objects.create(
        description=original_grn.description,
        customer=original_grn.customer,
        facility=original_grn.facility,
        document_type=original_grn.document_type,
        reference_number=original_grn.reference_number,
        supplier_name=original_grn.supplier_name,
        supplier_address=original_grn.supplier_address,
        supplier_phone=original_grn.supplier_phone,
        supplier_email=original_grn.supplier_email,
        grn_date=timezone.now().date(),
        expected_date=original_grn.expected_date,
        vessel=original_grn.vessel,
        voyage=original_grn.voyage,
        container_number=original_grn.container_number,
        seal_number=original_grn.seal_number,
        bl_number=original_grn.bl_number,
        status='draft',
        priority=original_grn.priority,
        notes=original_grn.notes,
        special_instructions=original_grn.special_instructions,
        created_by=request.user
    )
    
    # Copy GRN items
    for item in original_grn.items.all():
        GRNItem.objects.create(
            grn=new_grn,
            item=item.item,
            item_code=item.item_code,
            item_name=item.item_name,
            hs_code=item.hs_code,
            unit=item.unit,
            expected_qty=item.expected_qty,
            net_weight=item.net_weight,
            gross_weight=item.gross_weight,
            volume=item.volume,
            coo=item.coo,
            batch_number=item.batch_number,
            expiry_date=item.expiry_date,
            remark=item.remark
        )
    
    messages.success(request, f'GRN {original_grn.grn_number} duplicated successfully!')
    return redirect('grn:grn_detail', pk=new_grn.pk)


@login_required
def get_items_ajax(request):
    """AJAX view to get items for dropdown"""
    search_term = request.GET.get('search', '')
    items = Item.objects.filter(
        Q(item_code__icontains=search_term) |
        Q(item_name__icontains=search_term)
    )[:10]
    
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'item_code': item.item_code,
            'item_name': item.item_name,
            'hs_code': item.hs_code,
            'unit': item.unit,
        })
    
    return JsonResponse({'items': data})


@login_required
@require_http_methods(["GET"])
def get_job_data(request, job_id):
    """AJAX view to fetch job data for auto-population"""
    try:
        job = Job.objects.select_related(
            'customer_name', 'facility', 'assigned_to'
        ).prefetch_related('cargo_items__item', 'containers').get(id=job_id)
        
        # Get cargo items data
        cargo_items = []
        for cargo in job.cargo_items.all():
            cargo_items.append({
                'item_id': cargo.item.id if cargo.item else None,
                'item_code': cargo.item_code,
                'item_name': cargo.item.item_name if cargo.item else '',
                'hs_code': cargo.hs_code,
                'unit': cargo.unit,
                'quantity': float(cargo.quantity) if cargo.quantity else 0,
                'net_weight': float(cargo.net_weight) if cargo.net_weight else 0,
                'gross_weight': float(cargo.gross_weight) if cargo.gross_weight else 0,
                'coo': cargo.coo,
                'remark': cargo.remark,
            })
        
        # Get unique ED and CTNR values from job containers
        ed_values = list(job.containers.values_list('ed_number', flat=True).distinct().exclude(ed_number__isnull=True).exclude(ed_number=''))
        ctnr_values = list(job.containers.values_list('container_number', flat=True).distinct().exclude(container_number__isnull=True).exclude(container_number=''))
        
        data = {
            'success': True,
            'job': {
                'id': job.id,
                'customer_id': job.customer_name.id if job.customer_name else None,
                'customer_ref': job.customer_ref,
                'bl_number': job.bl_number,
                'mode': job.mode,
                'facility_id': job.facility.id if job.facility else None,
                'salesman_id': job.assigned_to.id if job.assigned_to else None,
                'salesman_name': job.assigned_to.get_full_name() if job.assigned_to else '',
                'total_quantity': float(job.total_quantity) if job.total_quantity else 0,
                'cargo_items': cargo_items,
                'ed_values': ed_values,
                'ctnr_values': ctnr_values,
            }
        }
        return JsonResponse(data)
    except Job.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def get_job_ed_ctnr_data(request, job_id):
    """AJAX view to fetch ED and CTNR data for dropdowns"""
    try:
        job = Job.objects.prefetch_related('containers').get(id=job_id)
        
        # Get unique ED and CTNR values from job containers
        ed_values = list(job.containers.values_list('ed_number', flat=True).distinct().exclude(ed_number__isnull=True).exclude(ed_number=''))
        ctnr_values = list(job.containers.values_list('container_number', flat=True).distinct().exclude(container_number__isnull=True).exclude(container_number=''))
        
        data = {
            'success': True,
            'ed_values': ed_values,
            'ctnr_values': ctnr_values,
        }
        return JsonResponse(data)
    except Job.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Print Views
@login_required
def grn_print_summary(request, pk):
    """Print GRN summary as PDF"""
    try:
        grn = get_object_or_404(GRN, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        html = render_to_string('grn/print/grn_summary.html', {
            'grn': grn,
            'company': company,
            'grn_items': grn.items.all(),
            'grn_pallets': grn.pallets.all()
        })
        
        # Generate PDF
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="GRN_Summary_{grn.grn_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('grn:grn_detail', pk=pk)


@login_required
def grn_print_detailed(request, pk):
    """Generate detailed GRN PDF"""
    grn = get_object_or_404(GRN, pk=pk)
    company = Company.objects.filter(is_active=True).first()
    
    # Get GRN items and pallets
    grn_items = grn.items.all()
    grn_pallets = grn.pallets.all()
    
    # Render the template
    html = render_to_string('grn/print/grn_detailed.html', {
        'grn': grn,
        'company': company,
        'grn_items': grn_items,
        'grn_pallets': grn_pallets,
    })
    
    # Generate PDF
    pdf = weasyprint.HTML(string=html).write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="GRN_{grn.grn_number}_Detailed.pdf"'
    
    return response


@login_required
def grn_print_putaways(request, pk):
    """Generate GRN putaways PDF"""
    grn = get_object_or_404(GRN, pk=pk)
    company = Company.objects.filter(is_active=True).first()
    
    # Get GRN pallets for putaways
    grn_pallets = grn.pallets.all()
    
    # Render the template
    html = render_to_string('grn/print/grn_putaways.html', {
        'grn': grn,
        'company': company,
        'grn_pallets': grn_pallets,
    })
    
    # Generate PDF
    pdf = weasyprint.HTML(string=html).write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="GRN_{grn.grn_number}_Putaways.pdf"'
    
    return response


# Email Views
@login_required
def grn_email(request, pk):
    """Email GRN as PDF attachment"""
    try:
        grn = get_object_or_404(GRN, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        if request.method == 'POST':
            email_to = request.POST.get('email_to')
            email_subject = request.POST.get('email_subject')
            email_message = request.POST.get('email_message')
            attach_summary = request.POST.get('attach_summary') == 'summary'
            attach_detailed = request.POST.get('attach_detailed') == 'detailed'
            attach_putaways = request.POST.get('attach_putaways') == 'putaways'
            
            if not email_to:
                messages.error(request, 'Email address is required.')
                return redirect('grn:grn_detail', pk=pk)
            
            # Create email
            email = EmailMessage(
                subject=email_subject,
                body=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_to]
            )
            
            # Attach PDFs based on selection
            if attach_summary:
                html_summary = render_to_string('grn/print/grn_summary.html', {
                    'grn': grn,
                    'company': company,
                    'grn_items': grn.items.all(),
                    'grn_pallets': grn.pallets.all()
                })
                pdf_summary = weasyprint.HTML(string=html_summary).write_pdf()
                email.attach(f'GRN_Summary_{grn.grn_number}.pdf', pdf_summary, 'application/pdf')
            
            if attach_detailed:
                html_detailed = render_to_string('grn/print/grn_detailed.html', {
                    'grn': grn,
                    'company': company,
                    'grn_items': grn.items.all(),
                    'grn_pallets': grn.pallets.all()
                })
                pdf_detailed = weasyprint.HTML(string=html_detailed).write_pdf()
                email.attach(f'GRN_Detailed_{grn.grn_number}.pdf', pdf_detailed, 'application/pdf')
            
            if attach_putaways:
                html_putaways = render_to_string('grn/print/grn_putaways.html', {
                    'grn': grn,
                    'company': company,
                    'grn_pallets': grn.pallets.all()
                })
                pdf_putaways = weasyprint.HTML(string=html_putaways).write_pdf()
                email.attach(f'GRN_Putaways_{grn.grn_number}.pdf', pdf_putaways, 'application/pdf')
            
            # If multiple are selected, create a combined PDF
            selected_attachments = []
            if attach_summary:
                selected_attachments.append(('summary', pdf_summary))
            if attach_detailed:
                selected_attachments.append(('detailed', pdf_detailed))
            if attach_putaways:
                selected_attachments.append(('putaways', pdf_putaways))
            
            if len(selected_attachments) > 1:
                merger = PdfMerger()
                pdf_files = []
                
                # Add all selected PDFs
                for attachment_type, pdf_content in selected_attachments:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.write(pdf_content)
                    temp_file.close()
                    pdf_files.append(temp_file.name)
                    merger.append(temp_file.name)
                
                # Create combined PDF
                output_buffer = BytesIO()
                merger.write(output_buffer)
                merger.close()
                output_buffer.seek(0)
                
                # Clean up temporary files
                for temp_file in pdf_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                
                # Remove individual attachments and add combined
                email.attachments = []
                email.attach(f'GRN_Complete_{grn.grn_number}.pdf', output_buffer.getvalue(), 'application/pdf')
            
            email.send()
            
            messages.success(request, f'GRN {grn.grn_number} has been sent via email.')
            return redirect('grn:grn_detail', pk=pk)
        else:
            messages.error(request, 'Invalid request method.')
            return redirect('grn:grn_detail', pk=pk)
            
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('grn:grn_detail', pk=pk)
