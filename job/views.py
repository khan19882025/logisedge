from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Job, JobStatus, JobPriority
from .forms import JobForm, JobSearchForm, JobCargoFormSet, CustomJobCargoFormSet, CustomJobContainerFormSet
from customer.models import Customer
from items.models import Item
from company.company_model import Company



class JobListView(LoginRequiredMixin, ListView):
    """View for listing all jobs with search and filtering"""
    model = Job
    template_name = 'job/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 20

    def get_queryset(self):
        queryset = Job.objects.select_related(
            'status', 'priority', 'assigned_to', 'created_by'
        ).prefetch_related('related_items', 'related_facilities')
        
        # Get search parameters
        form = JobSearchForm(self.request.GET)
        if form.is_valid():
            search_term = form.cleaned_data.get('search_term')
            search_field = form.cleaned_data.get('search_field', 'title')
            job_type = form.cleaned_data.get('job_type')
            status = form.cleaned_data.get('status')
            priority = form.cleaned_data.get('priority')
            mode = form.cleaned_data.get('mode')
            assigned_to = form.cleaned_data.get('assigned_to')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            overdue_only = form.cleaned_data.get('overdue_only')
            
            # Apply filters
            if search_term:
                if search_field == 'title':
                    queryset = queryset.filter(title__icontains=search_term)
                elif search_field == 'description':
                    queryset = queryset.filter(description__icontains=search_term)
                elif search_field == 'job_code':
                    queryset = queryset.filter(job_code__icontains=search_term)
                elif search_field == 'notes':
                    queryset = queryset.filter(notes__icontains=search_term)
            
            if job_type:
                queryset = queryset.filter(job_type=job_type)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if mode:
                queryset = queryset.filter(mode=mode)
            
            if assigned_to:
                queryset = queryset.filter(assigned_to=assigned_to)
            
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            
            if overdue_only:
                queryset = queryset.filter(
                    due_date__lt=timezone.now(),
                    status__name__in=['pending', 'in progress', 'review']
                )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = JobSearchForm(self.request.GET)
        
        # Add statistics
        context['total_jobs'] = Job.objects.count()
        context['pending_jobs'] = Job.objects.filter(status__name__icontains='pending').count()
        context['in_progress_jobs'] = Job.objects.filter(status__name__icontains='in progress').count()
        context['completed_jobs'] = Job.objects.filter(status__name__icontains='completed').count()
        context['overdue_jobs'] = Job.objects.filter(
            due_date__lt=timezone.now(),
            status__name__in=['pending', 'in progress', 'review']
        ).count()
        
        return context


class JobDetailView(LoginRequiredMixin, DetailView):
    """View for displaying job details"""
    model = Job
    template_name = 'job/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add related data
        context['related_jobs'] = Job.objects.filter(
            Q(assigned_to=self.object.assigned_to) | 
            Q(job_type=self.object.job_type)
        ).exclude(id=self.object.id)[:5]
        return context


class JobCreateView(LoginRequiredMixin, CreateView):
    """View for creating new jobs"""
    model = Job
    form_class = JobForm
    template_name = 'job/job_form.html'
    success_url = reverse_lazy('job:job_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cargo_formset'] = CustomJobCargoFormSet(self.request.POST, instance=self.object)
            context['container_formset'] = CustomJobContainerFormSet(self.request.POST, instance=self.object)
        else:
            # For new jobs, create formset with a temporary instance
            if not self.object:
                self.object = Job()
            context['cargo_formset'] = CustomJobCargoFormSet(instance=self.object)
            context['container_formset'] = CustomJobContainerFormSet(instance=self.object)
        context['title'] = 'Create New Job'
        context['submit_text'] = 'Create Job'
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        print("=== JOB CREATE POST METHOD CALLED ===")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"POST data: {dict(request.POST)}")
        
        self.object = None
        form = self.get_form()
        cargo_formset = CustomJobCargoFormSet(self.request.POST)
        container_formset = CustomJobContainerFormSet(self.request.POST)
        
        print(f"Form is valid: {form.is_valid()}")
        print(f"Cargo formset is valid: {cargo_formset.is_valid()}")
        print(f"Container formset is valid: {container_formset.is_valid()}")
        
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        if not cargo_formset.is_valid():
            print(f"Cargo formset errors: {cargo_formset.errors}")
        if not container_formset.is_valid():
            print(f"Container formset errors: {container_formset.errors}")
            print(f"Container formset non_form_errors: {container_formset.non_form_errors()}")
            for i, form in enumerate(container_formset.forms):
                if form.errors:
                    print(f"Container form {i} errors: {form.errors}")
                print(f"Container form {i} data: {form.data if hasattr(form, 'data') else 'No data'}")
                print(f"Container form {i} cleaned_data: {getattr(form, 'cleaned_data', 'No cleaned_data')}")
                print(f"Container form {i} is_valid: {form.is_valid()}")
                if hasattr(form, 'instance'):
                    print(f"Container form {i} instance: {form.instance}")
            print(f"Container formset management form data: {container_formset.management_form.data}")
            print(f"Container formset management form errors: {container_formset.management_form.errors}")
        
        if form.is_valid() and cargo_formset.is_valid() and container_formset.is_valid():
            return self.form_valid(form, cargo_formset, container_formset)
        else:
            return self.form_invalid(form, cargo_formset, container_formset)

    def form_valid(self, form, cargo_formset, container_formset):
        self.object = form.save()
        cargo_formset.instance = self.object
        cargo_formset.save()
        container_formset.instance = self.object
        container_formset.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form, cargo_formset, container_formset):
        return self.render_to_response(
            self.get_context_data(form=form, cargo_formset=cargo_formset, container_formset=container_formset)
        )


class JobUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating existing jobs"""
    model = Job
    form_class = JobForm
    template_name = 'job/job_form.html'
    success_url = reverse_lazy('job:job_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cargo_formset'] = CustomJobCargoFormSet(self.request.POST, instance=self.object)
        else:
            context['cargo_formset'] = CustomJobCargoFormSet(instance=self.object)
        
        context['title'] = f'Edit Job - {self.object.job_code}'
        context['submit_text'] = 'Update Job'
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        cargo_formset = CustomJobCargoFormSet(self.request.POST, instance=self.object)
        
        if form.is_valid() and cargo_formset.is_valid():
            return self.form_valid(form, cargo_formset)
        else:
            return self.form_invalid(form, cargo_formset)

    def form_valid(self, form, cargo_formset):
        self.object = form.save()
        cargo_formset.instance = self.object
        cargo_formset.save()
        messages.success(self.request, 'Job updated successfully!')
        return redirect(self.get_success_url())

    def form_invalid(self, form, cargo_formset):
        return self.render_to_response(
            self.get_context_data(form=form, cargo_formset=cargo_formset)
        )


class JobEditView(LoginRequiredMixin, UpdateView):
    """Separate view for editing existing jobs with dedicated template"""
    model = Job
    form_class = JobForm
    template_name = 'job/job_edit.html'

    def get_success_url(self):
        return reverse_lazy('job:job_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cargo_formset'] = CustomJobCargoFormSet(self.request.POST, instance=self.object)
            context['container_formset'] = CustomJobContainerFormSet(self.request.POST, instance=self.object)
        else:
            context['cargo_formset'] = CustomJobCargoFormSet(instance=self.object)
            context['container_formset'] = CustomJobContainerFormSet(instance=self.object)
        
        context['title'] = f'Edit Job - {self.object.job_code}'
        context['submit_text'] = 'Update Job'
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        cargo_formset = CustomJobCargoFormSet(self.request.POST, instance=self.object)
        container_formset = CustomJobContainerFormSet(self.request.POST, instance=self.object)
        
        if form.is_valid() and cargo_formset.is_valid() and container_formset.is_valid():
            return self.form_valid(form, cargo_formset, container_formset)
        else:
            return self.form_invalid(form, cargo_formset, container_formset)

    def form_valid(self, form, cargo_formset, container_formset):
        self.object = form.save()
        cargo_formset.instance = self.object
        cargo_formset.save()
        container_formset.instance = self.object
        container_formset.save()
        messages.success(self.request, f'Job {self.object.job_code} updated successfully.')
        return redirect(self.get_success_url())

    def form_invalid(self, form, cargo_formset, container_formset):
        return self.render_to_response(
            self.get_context_data(form=form, cargo_formset=cargo_formset, container_formset=container_formset)
        )


class JobDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting jobs"""
    model = Job
    template_name = 'job/job_confirm_delete.html'
    success_url = reverse_lazy('job:job_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Job deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def job_quick_view(request, pk):
    """Quick view for job details in modal"""
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'job/job_quick_view.html', {'job': job})


@login_required
def job_export(request):
    """Export jobs to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Job Code', 'Title', 'Type', 'Status', 'Priority', 
        'Assigned To', 'Created By', 'Due Date', 'Created At'
    ])
    
    jobs = Job.objects.select_related(
        'status', 'priority', 'assigned_to', 'created_by'
    ).all()
    
    for job in jobs:
        writer.writerow([
            job.job_code,
            job.title,
            job.job_type.name if job.job_type else '',
            job.status.name if job.status else '',
            job.priority.name if job.priority else '',
            job.assigned_to.get_full_name() if job.assigned_to else '',
            job.created_by.get_full_name() if job.created_by else '',
            job.due_date.strftime('%Y-%m-%d %H:%M') if job.due_date else '',
            job.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


def get_customer_salesman(request, customer_id):
    """Get salesman data for a selected customer"""
    try:
        customer = Customer.objects.get(id=customer_id)
        if customer.salesman:
            salesman_data = {
                'id': customer.salesman.id,
                'name': customer.salesman.get_full_name(),
                'code': customer.salesman.salesman_code
            }
            return JsonResponse({'success': True, 'salesman': salesman_data})
        else:
            return JsonResponse({'success': True, 'salesman': None})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_item_data(request, item_id):
    """Get item data for auto-population"""
    try:
        item = Item.objects.get(id=item_id)
        item_data = {
            'id': item.id,
            'item_code': item.item_code,
            'item_name': item.item_name,
            'unit_of_measure': item.unit_of_measure,
            'description': item.description or item.short_description or item.item_name
        }
        return JsonResponse({'success': True, 'item': item_data})
    except Item.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_items_list(request):
    """Get list of all active items for dropdown"""
    try:
        items = Item.objects.filter(status='active').order_by('item_name')
        items_list = [{'id': item.id, 'name': f"{item.item_name} ({item.item_code})"} for item in items]
        return JsonResponse({'success': True, 'items': items_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class JobPrintView(LoginRequiredMixin, DetailView):
    """View for printing job details as PDF"""
    model = Job
    template_name = 'job/job_print.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add company details
        context['company'] = Company.objects.filter(is_active=True).first()
        # Add related jobs if needed
        context['related_jobs'] = Job.objects.filter(
            Q(assigned_to=self.object.assigned_to) | 
            Q(job_type=self.object.job_type)
        ).exclude(id=self.object.id)[:5]
        return context


@login_required
def get_customer_jobs(request, customer_id):
    """Get jobs for a specific customer for Cross Stuffing"""
    try:
        jobs = Job.objects.filter(
            customer_name_id=customer_id,
            job_type="Cross Stuffing"
        ).order_by('job_code')
        
        jobs_data = [{
            'id': job.id,
            'job_code': job.job_code,
            'title': job.title,
            'status': job.status.name if job.status else '',
            'created_at': job.created_at.strftime('%Y-%m-%d') if job.created_at else ''
        } for job in jobs]
        
        return JsonResponse({'success': True, 'jobs': jobs_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_job_details(request, pk):
    """Get detailed job information including containers and cargo for Cross Stuffing"""
    try:
        job = Job.objects.get(pk=pk)
        
        # Get containers for this job
        containers = []
        if hasattr(job, 'containers'):
            for container in job.containers.all():
                containers.append({
                    'container_number': container.container_number,
                    'container_size': container.container_size,
                    'seal_number': container.seal_number,
                    'ed_number': container.ed_number
                })
        
        # Get cargo items for this job
        cargo_items = []
        if hasattr(job, 'cargo_items'):
            for cargo in job.cargo_items.all():
                cargo_items.append({
                    'item_name': cargo.item.item_name if cargo.item else cargo.item_code,
                    'quantity': cargo.quantity,
                    'unit': cargo.unit,
                    'hs_code': cargo.hs_code
                })
        
        job_data = {
            'id': job.id,
            'job_code': job.job_code,
            'title': job.title,
            'containers': containers,
            'cargo_items': cargo_items
        }
        
        # Debug logging
        print(f"[DEBUG] Job {job.job_code} data:")
        print(f"[DEBUG] Containers: {containers}")
        print(f"[DEBUG] Cargo items: {cargo_items}")
        print(f"[DEBUG] Final job_data: {job_data}")
        
        return JsonResponse({'success': True, 'job': job_data})
    except Job.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job not found'})
    except Exception as e:
        print(f"[DEBUG] Error in get_job_details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})