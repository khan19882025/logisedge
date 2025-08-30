from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
import json
from .models import Documentation, DocumentationCargo
from .forms import DocumentationForm
from job.models import Job, JobCargo
from customer.models import Customer
from company.company_model import Company
from django.db import models
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import weasyprint
from io import BytesIO


class DocumentationListView(LoginRequiredMixin, ListView):
    """View for listing all documentation"""
    model = Documentation
    template_name = 'documentation/documentation_list.html'
    context_object_name = 'documentations'
    paginate_by = 20


class DocumentationDetailView(LoginRequiredMixin, DetailView):
    """View for displaying documentation details"""
    model = Documentation
    template_name = 'documentation/documentation_detail.html'
    context_object_name = 'documentation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add cargo items to context
        context['cargo_items'] = self.object.cargo_items.all()
        return context


class DocumentationCreateView(LoginRequiredMixin, CreateView):
    """View for creating new documentation"""
    model = Documentation
    form_class = DocumentationForm
    template_name = 'documentation/documentation_form.html'
    success_url = reverse_lazy('documentation:documentation_list')

    def form_valid(self, form):
        # Debug: Print form data
        print("Form data received:")
        print(f"bill_to: {form.cleaned_data.get('bill_to')}")
        print(f"bill_to_address: {form.cleaned_data.get('bill_to_address')}")
        print(f"All form data: {form.cleaned_data}")
        
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Save selected cargo items
        self.save_cargo_items(form.instance)
        
        messages.success(self.request, 'Documentation created successfully!')
        return response
    
    def save_cargo_items(self, documentation):
        """Save selected cargo items to the documentation"""
        cargo_data = self.request.POST.get('selected_cargo_items')
        if cargo_data:
            try:
                cargo_items = json.loads(cargo_data)
                first_job_code = None
                
                for cargo_item in cargo_items:
                    # Get the original job cargo
                    job_cargo = JobCargo.objects.get(id=cargo_item['id'])
                    
                    # Set job_no from the first cargo item's job
                    if first_job_code is None:
                        first_job_code = job_cargo.job.job_code
                        documentation.job_no = first_job_code
                        documentation.save()
                    
                    # Create documentation cargo item
                    DocumentationCargo.objects.create(
                        documentation=documentation,
                        job_cargo=job_cargo,
                        item_name=cargo_item.get('item_name', ''),
                        item_code=cargo_item.get('item_code', ''),
                        hs_code=cargo_item.get('hs_code', ''),
                        unit=cargo_item.get('unit', ''),
                        quantity=cargo_item.get('quantity', 0),
                        coo=cargo_item.get('coo', ''),
                        net_weight=cargo_item.get('n_weight', None),
                        gross_weight=cargo_item.get('g_weight', None),
                        rate=cargo_item.get('rate', None),
                        amount=cargo_item.get('amount', None),
                    )
            except (json.JSONDecodeError, JobCargo.DoesNotExist) as e:
                print(f"Error saving cargo items: {e}")


class DocumentationUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating existing documentation"""
    model = Documentation
    form_class = DocumentationForm
    template_name = 'documentation/documentation_form.html'
    success_url = reverse_lazy('documentation:documentation_list')

    def form_valid(self, form):
        # Debug: Print form data
        print("Update form data received:")
        print(f"bill_to: {form.cleaned_data.get('bill_to')}")
        print(f"bill_to_address: {form.cleaned_data.get('bill_to_address')}")
        print(f"All form data: {form.cleaned_data}")
        
        response = super().form_valid(form)
        
        # Clear existing cargo items and save new ones
        form.instance.cargo_items.all().delete()
        self.save_cargo_items(form.instance)
        
        messages.success(self.request, 'Documentation updated successfully!')
        return response
    
    def save_cargo_items(self, documentation):
        """Save selected cargo items to the documentation"""
        cargo_data = self.request.POST.get('selected_cargo_items')
        if cargo_data:
            try:
                cargo_items = json.loads(cargo_data)
                first_job_code = None
                
                for cargo_item in cargo_items:
                    # Get the original job cargo
                    job_cargo = JobCargo.objects.get(id=cargo_item['id'])
                    
                    # Set job_no from the first cargo item's job
                    if first_job_code is None:
                        first_job_code = job_cargo.job.job_code
                        documentation.job_no = first_job_code
                        documentation.save()
                    
                    # Create documentation cargo item
                    DocumentationCargo.objects.create(
                        documentation=documentation,
                        job_cargo=job_cargo,
                        item_name=cargo_item.get('item_name', ''),
                        item_code=cargo_item.get('item_code', ''),
                        hs_code=cargo_item.get('hs_code', ''),
                        unit=cargo_item.get('unit', ''),
                        quantity=cargo_item.get('quantity', 0),
                        coo=cargo_item.get('coo', ''),
                        net_weight=cargo_item.get('n_weight', None),
                        gross_weight=cargo_item.get('g_weight', None),
                        rate=cargo_item.get('rate', None),
                        amount=cargo_item.get('amount', None),
                    )
            except (json.JSONDecodeError, JobCargo.DoesNotExist) as e:
                print(f"Error saving cargo items: {e}")


class DocumentationDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting documentation"""
    model = Documentation
    template_name = 'documentation/documentation_confirm_delete.html'
    success_url = reverse_lazy('documentation:documentation_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Documentation deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def get_customer_cargo(request, customer_id):
    """AJAX view to get cargo items for a specific customer with remaining balance"""
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        
        # Get all jobs for this customer with job_type="Documentations"
        jobs = Job.objects.filter(
            customer_name=customer,
            job_type="Documentations"
        ).prefetch_related('cargo_items', 'cargo_items__item', 'containers')
        
        cargo_items = []
        for job in jobs:
            # Get ED number from the first container (if any)
            ed_number = None
            if job.containers.exists():
                ed_number = job.containers.first().ed_number
            
            for cargo in job.cargo_items.all():
                # Calculate how much of this cargo has already been used in documentation
                used_quantity = DocumentationCargo.objects.filter(
                    job_cargo=cargo
                ).aggregate(
                    total_used=models.Sum('quantity')
                )['total_used'] or 0
                
                # Calculate remaining balance
                original_quantity = cargo.quantity or 0
                remaining_quantity = original_quantity - used_quantity
                
                # Only include cargo items that have remaining quantity
                if remaining_quantity > 0:
                    # Calculate proportional weights and amounts for remaining quantity
                    remaining_ratio = remaining_quantity / original_quantity if original_quantity > 0 else 0
                    
                    remaining_net_weight = None
                    remaining_gross_weight = None
                    remaining_amount = None
                    
                    if cargo.net_weight:
                        remaining_net_weight = cargo.net_weight * remaining_ratio
                    if cargo.gross_weight:
                        remaining_gross_weight = cargo.gross_weight * remaining_ratio
                    if cargo.amount:
                        remaining_amount = cargo.amount * remaining_ratio
                    
                    cargo_items.append({
                        'id': cargo.id,
                        'job_id': job.id,
                        'job_code': job.job_code,
                        'item_name': cargo.item.item_name if cargo.item else None,
                        'item_code': cargo.item_code,
                        'quantity': str(remaining_quantity),  # Show remaining quantity
                        'original_quantity': str(original_quantity),  # Keep original for reference
                        'used_quantity': str(used_quantity),  # How much already used
                        'unit': cargo.unit,
                        'hs_code': cargo.hs_code,
                        'coo': cargo.coo,
                        'n_weight': str(remaining_net_weight) if remaining_net_weight else None,
                        'g_weight': str(remaining_gross_weight) if remaining_gross_weight else None,
                        'rate': str(cargo.rate) if cargo.rate else None,
                        'amount': str(remaining_amount) if remaining_amount else None,
                        'ed': ed_number or None,
                    })
        
        return JsonResponse({
            'success': True,
            'cargo_items': cargo_items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# Print Views
@login_required
def print_invoice(request, pk):
    """Print invoice as PDF"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Optimize query with select_related and prefetch_related
        documentation = Documentation.objects.select_related(
            'customer', 'created_by'
        ).prefetch_related(
            'cargo_items__job_cargo__job__containers'
        ).get(pk=pk)
        
        html = render_to_string('documentation/print/invoice.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        
        # Generate PDF with optimized settings
        pdf = weasyprint.HTML(string=html).write_pdf(
            optimize_size=('fonts', 'images'),
            presentational_hints=True
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Invoice_{documentation.document_no}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


@login_required
def print_packing_list(request, pk):
    """Print packing list as PDF"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Optimize query with select_related and prefetch_related
        documentation = Documentation.objects.select_related(
            'customer', 'created_by'
        ).prefetch_related(
            'cargo_items__job_cargo__job__containers'
        ).get(pk=pk)
        
        html = render_to_string('documentation/print/packing_list.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        
        # Generate PDF with optimized settings
        pdf = weasyprint.HTML(string=html).write_pdf(
            optimize_size=('fonts', 'images'),
            presentational_hints=True
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="PackingList_{documentation.document_no}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


@login_required
def print_da(request, pk):
    """Print DA (Delivery Authorization) as PDF"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Optimize query with select_related and prefetch_related
        documentation = Documentation.objects.select_related(
            'customer', 'created_by'
        ).prefetch_related(
            'cargo_items__job_cargo__job__containers'
        ).get(pk=pk)
        
        html = render_to_string('documentation/print/da.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        
        # Generate PDF with optimized settings
        pdf = weasyprint.HTML(string=html).write_pdf(
            optimize_size=('fonts', 'images'),
            presentational_hints=True
        )
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="DA_{documentation.document_no}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


@login_required
def print_too_letter(request, pk):
    """Print TOO letter as PDF"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        html = render_to_string('documentation/print/too_letter.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        
        # Generate PDF
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="TOOLetter_{documentation.document_no}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


# Email Views
@login_required
def email_invoice(request, pk):
    """Email invoice as PDF attachment"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('documentation/print/invoice.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'Invoice - {documentation.document_no}'
        message = f'Please find attached the invoice for documentation {documentation.document_no}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[documentation.customer.email] if documentation.customer and documentation.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'Invoice_{documentation.document_no}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'Invoice for {documentation.document_no} has been sent via email.')
        return redirect('documentation:documentation_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


@login_required
def email_packing_list(request, pk):
    """Email packing list as PDF attachment"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('documentation/print/packing_list.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'Packing List - {documentation.document_no}'
        message = f'Please find attached the packing list for documentation {documentation.document_no}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[documentation.customer.email] if documentation.customer and documentation.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'PackingList_{documentation.document_no}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'Packing list for {documentation.document_no} has been sent via email.')
        return redirect('documentation:documentation_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


@login_required
def email_da(request, pk):
    """Email DA (Delivery Authorization) as PDF attachment"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('documentation/print/da.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'Delivery Authorization - {documentation.document_no}'
        message = f'Please find attached the delivery authorization for documentation {documentation.document_no}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[documentation.customer.email] if documentation.customer and documentation.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'DA_{documentation.document_no}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'Delivery Authorization for {documentation.document_no} has been sent via email.')
        return redirect('documentation:documentation_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


@login_required
def email_too_letter(request, pk):
    """Email TOO letter as PDF attachment"""
    try:
        documentation = get_object_or_404(Documentation, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('documentation/print/too_letter.html', {
            'documentation': documentation,
            'company': company,
            'cargo_items': documentation.cargo_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'TOO Letter - {documentation.document_no}'
        message = f'Please find attached the TOO letter for documentation {documentation.document_no}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[documentation.customer.email] if documentation.customer and documentation.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'TOOLetter_{documentation.document_no}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'TOO Letter for {documentation.document_no} has been sent via email.')
        return redirect('documentation:documentation_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('documentation:documentation_detail', pk=pk)


# Bulk Operations
@login_required
def bulk_print(request):
    """Bulk print multiple document types"""
    if request.method == 'POST':
        try:
            documentation_id = request.POST.get('documentation_id')
            selected_documents = request.POST.getlist('documents')
            combine_pdf = request.POST.get('combine_pdf') == 'on'
            
            print(f"DEBUG: documentation_id={documentation_id}, selected_documents={selected_documents}, combine_pdf={combine_pdf}")
            
            if not documentation_id or not selected_documents:
                messages.error(request, 'Please select at least one document to print.')
                return redirect('documentation:documentation_detail', pk=documentation_id)
            
            documentation = get_object_or_404(Documentation, pk=documentation_id)
            company = Company.objects.filter(is_active=True).first()
            
            print(f"DEBUG: Found documentation: {documentation.document_no}, company: {company}")
            
            if combine_pdf:
                print("DEBUG: Combining PDFs")
                # Combine all selected documents into one PDF
                from PyPDF2 import PdfMerger
                import tempfile
                import os
                
                merger = PdfMerger()
                pdf_files = []
                
                for doc_type in selected_documents:
                    print(f"DEBUG: Processing document type: {doc_type}")
                    if doc_type == 'invoice':
                        html = render_to_string('documentation/print/invoice.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    elif doc_type == 'packing_list':
                        html = render_to_string('documentation/print/packing_list.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    elif doc_type == 'da':
                        html = render_to_string('documentation/print/da.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    elif doc_type == 'too_letter':
                        html = render_to_string('documentation/print/too_letter.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    else:
                        print(f"DEBUG: Unknown document type: {doc_type}")
                        continue
                    
                    print(f"DEBUG: Generating PDF for {doc_type}")
                    # Generate PDF
                    pdf = weasyprint.HTML(string=html).write_pdf()
                    
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.write(pdf)
                    temp_file.close()
                    pdf_files.append(temp_file.name)
                    merger.append(temp_file.name)
                    print(f"DEBUG: Added {doc_type} to merger")
                
                print("DEBUG: Creating combined PDF")
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
                
                print("DEBUG: Returning combined PDF response")
                # Return combined PDF
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="Combined_Documents_{documentation.document_no}.pdf"'
                return response
            else:
                # Return first selected document (for simplicity, you could implement zip download)
                doc_type = selected_documents[0]
                print(f"DEBUG: Generating single PDF for {doc_type}")
                
                if doc_type == 'invoice':
                    html = render_to_string('documentation/print/invoice.html', {
                        'documentation': documentation,
                        'company': company,
                        'cargo_items': documentation.cargo_items.all()
                    })
                    filename = f'Invoice_{documentation.document_no}.pdf'
                elif doc_type == 'packing_list':
                    html = render_to_string('documentation/print/packing_list.html', {
                        'documentation': documentation,
                        'company': company,
                        'cargo_items': documentation.cargo_items.all()
                    })
                    filename = f'PackingList_{documentation.document_no}.pdf'
                elif doc_type == 'da':
                    html = render_to_string('documentation/print/da.html', {
                        'documentation': documentation,
                        'company': company,
                        'cargo_items': documentation.cargo_items.all()
                    })
                    filename = f'DA_{documentation.document_no}.pdf'
                elif doc_type == 'too_letter':
                    html = render_to_string('documentation/print/too_letter.html', {
                        'documentation': documentation,
                        'company': company,
                        'cargo_items': documentation.cargo_items.all()
                    })
                    filename = f'TOOLetter_{documentation.document_no}.pdf'
                else:
                    messages.error(request, f'Unknown document type: {doc_type}')
                    return redirect('documentation:documentation_detail', pk=documentation_id)
                
                print(f"DEBUG: Generating PDF for {doc_type}")
                # Generate PDF
                pdf = weasyprint.HTML(string=html).write_pdf()
                
                print(f"DEBUG: Returning single PDF response: {filename}")
                # Return PDF
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
        except Exception as e:
            print(f"DEBUG: Error in bulk_print: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error generating bulk PDF: {str(e)}')
            return redirect('documentation:documentation_detail', pk=documentation_id)
    
    return redirect('documentation:documentation_list')


@login_required
def bulk_email(request):
    """Bulk email multiple document types"""
    if request.method == 'POST':
        try:
            documentation_id = request.POST.get('documentation_id')
            selected_documents = request.POST.getlist('documents')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            recipients = request.POST.get('recipients')
            combine_pdf = request.POST.get('combine_pdf') == 'on'
            
            if not documentation_id or not selected_documents:
                messages.error(request, 'Please select at least one document to email.')
                return redirect('documentation:documentation_detail', pk=documentation_id)
            
            if not subject or not message or not recipients:
                messages.error(request, 'Please fill in all required fields.')
                return redirect('documentation:documentation_detail', pk=documentation_id)
            
            documentation = get_object_or_404(Documentation, pk=documentation_id)
            company = Company.objects.filter(is_active=True).first()
            
            # Parse recipients
            recipient_list = [email.strip() for email in recipients.split(',') if email.strip()]
            
            if combine_pdf:
                # Combine all selected documents into one PDF
                from PyPDF2 import PdfMerger
                import tempfile
                import os
                
                merger = PdfMerger()
                pdf_files = []
                
                for doc_type in selected_documents:
                    if doc_type == 'invoice':
                        html = render_to_string('documentation/print/invoice.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    elif doc_type == 'packing_list':
                        html = render_to_string('documentation/print/packing_list.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    elif doc_type == 'da':
                        html = render_to_string('documentation/print/da.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    elif doc_type == 'too_letter':
                        html = render_to_string('documentation/print/too_letter.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                    else:
                        continue
                    
                    # Generate PDF
                    pdf = weasyprint.HTML(string=html).write_pdf()
                    
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.write(pdf)
                    temp_file.close()
                    pdf_files.append(temp_file.name)
                    merger.append(temp_file.name)
                
                # Create combined PDF
                output_buffer = BytesIO()
                merger.write(output_buffer)
                merger.close()
                output_buffer.seek(0)
                
                # Create email
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=recipient_list
                )
                
                email.attach(f'Combined_Documents_{documentation.document_no}.pdf', output_buffer.getvalue(), 'application/pdf')
                email.send()
                
                # Clean up temporary files
                for temp_file in pdf_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                
                messages.success(request, f'Combined documents for {documentation.document_no} have been sent via email.')
            else:
                # Send separate emails for each document
                for doc_type in selected_documents:
                    if doc_type == 'invoice':
                        html = render_to_string('documentation/print/invoice.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                        filename = f'Invoice_{documentation.document_no}.pdf'
                    elif doc_type == 'packing_list':
                        html = render_to_string('documentation/print/packing_list.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                        filename = f'PackingList_{documentation.document_no}.pdf'
                    elif doc_type == 'da':
                        html = render_to_string('documentation/print/da.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                        filename = f'DA_{documentation.document_no}.pdf'
                    elif doc_type == 'too_letter':
                        html = render_to_string('documentation/print/too_letter.html', {
                            'documentation': documentation,
                            'company': company,
                            'cargo_items': documentation.cargo_items.all()
                        })
                        filename = f'TOOLetter_{documentation.document_no}.pdf'
                    else:
                        continue
                    
                    pdf = weasyprint.HTML(string=html).write_pdf()
                    
                    email = EmailMessage(
                        subject=f"{subject} - {doc_type.replace('_', ' ').title()}",
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=recipient_list
                    )
                    
                    email.attach(filename, pdf, 'application/pdf')
                    email.send()
                
                messages.success(request, f'Documents for {documentation.document_no} have been sent via email.')
            
            return redirect('documentation:documentation_detail', pk=documentation_id)
            
        except Exception as e:
            messages.error(request, f'Error sending bulk email: {str(e)}')
            return redirect('documentation:documentation_detail', pk=documentation_id)
    
    return redirect('documentation:documentation_list')