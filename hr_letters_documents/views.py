from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
from datetime import datetime, timedelta

from .models import (
    LetterType, LetterTemplate, GeneratedLetter, LetterPlaceholder,
    LetterApproval, DocumentCategory, HRDocument, LetterHistory
)
from .forms import (
    LetterTypeForm, LetterTemplateForm, LetterGenerationForm, LetterEditForm,
    LetterApprovalForm, LetterSearchForm, DocumentCategoryForm, HRDocumentForm,
    DocumentSearchForm, LetterPlaceholderForm, LetterPreviewForm, BulkLetterGenerationForm
)
from employees.models import Employee


@login_required
@permission_required('hr_letters_documents.view_generatedletter')
def dashboard(request):
    """Dashboard view for HR Letters & Documents"""
    # Get statistics
    total_letters = GeneratedLetter.objects.count()
    draft_letters = GeneratedLetter.objects.filter(status='draft').count()
    finalized_letters = GeneratedLetter.objects.filter(status='finalized').count()
    signed_letters = GeneratedLetter.objects.filter(status='signed').count()
    
    # Recent letters
    recent_letters = GeneratedLetter.objects.select_related('employee', 'letter_type').order_by('-created_at')[:5]
    
    # Letters by type
    letters_by_type = LetterType.objects.annotate(
        letter_count=Count('generatedletter')
    ).order_by('-letter_count')[:5]
    
    # Letters by status
    letters_by_status = GeneratedLetter.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Recent documents
    recent_documents = HRDocument.objects.select_related('category').order_by('-uploaded_at')[:5]
    
    context = {
        'total_letters': total_letters,
        'draft_letters': draft_letters,
        'finalized_letters': finalized_letters,
        'signed_letters': signed_letters,
        'recent_letters': recent_letters,
        'letters_by_type': letters_by_type,
        'letters_by_status': letters_by_status,
        'recent_documents': recent_documents,
    }
    
    return render(request, 'hr_letters_documents/dashboard.html', context)


# Letter Type Views
class LetterTypeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LetterType
    template_name = 'hr_letters_documents/letter_type_list.html'
    context_object_name = 'letter_types'
    permission_required = 'hr_letters_documents.view_lettertype'
    
    def get_queryset(self):
        queryset = LetterType.objects.all().order_by('name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class LetterTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LetterType
    form_class = LetterTypeForm
    template_name = 'hr_letters_documents/letter_type_form.html'
    permission_required = 'hr_letters_documents.add_lettertype'
    success_url = reverse_lazy('hr_letters_documents:letter_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Letter type created successfully.')
        return super().form_valid(form)


class LetterTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LetterType
    form_class = LetterTypeForm
    template_name = 'hr_letters_documents/letter_type_form.html'
    permission_required = 'hr_letters_documents.change_lettertype'
    success_url = reverse_lazy('hr_letters_documents:letter_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Letter type updated successfully.')
        return super().form_valid(form)


class LetterTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LetterType
    template_name = 'hr_letters_documents/letter_type_confirm_delete.html'
    permission_required = 'hr_letters_documents.delete_lettertype'
    success_url = reverse_lazy('hr_letters_documents:letter_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Letter type deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Letter Template Views
class LetterTemplateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LetterTemplate
    template_name = 'hr_letters_documents/letter_template_list.html'
    context_object_name = 'templates'
    permission_required = 'hr_letters_documents.view_lettertemplate'
    
    def get_queryset(self):
        queryset = LetterTemplate.objects.select_related('letter_type').all().order_by('letter_type__name', 'language')
        search = self.request.GET.get('search')
        letter_type = self.request.GET.get('letter_type')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(subject__icontains=search)
            )
        if letter_type:
            queryset = queryset.filter(letter_type_id=letter_type)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['letter_types'] = LetterType.objects.filter(is_active=True)
        return context


class LetterTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LetterTemplate
    form_class = LetterTemplateForm
    template_name = 'hr_letters_documents/letter_template_form.html'
    permission_required = 'hr_letters_documents.add_lettertemplate'
    success_url = reverse_lazy('hr_letters_documents:letter_template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Letter template created successfully.')
        return super().form_valid(form)


class LetterTemplateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LetterTemplate
    form_class = LetterTemplateForm
    template_name = 'hr_letters_documents/letter_template_form.html'
    permission_required = 'hr_letters_documents.change_lettertemplate'
    success_url = reverse_lazy('hr_letters_documents:letter_template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Letter template updated successfully.')
        return super().form_valid(form)


class LetterTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LetterTemplate
    template_name = 'hr_letters_documents/letter_template_confirm_delete.html'
    permission_required = 'hr_letters_documents.delete_lettertemplate'
    success_url = reverse_lazy('hr_letters_documents:letter_template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Letter template deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Generated Letter Views
class GeneratedLetterListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = GeneratedLetter
    template_name = 'hr_letters_documents/generated_letter_list.html'
    context_object_name = 'letters'
    permission_required = 'hr_letters_documents.view_generatedletter'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = GeneratedLetter.objects.select_related(
            'employee', 'letter_type', 'template', 'created_by'
        ).all().order_by('-created_at')
        
        form = LetterSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            letter_type = form.cleaned_data.get('letter_type')
            status = form.cleaned_data.get('status')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            created_by = form.cleaned_data.get('created_by')
            
            if search:
                queryset = queryset.filter(
                    Q(reference_number__icontains=search) |
                    Q(employee__full_name__icontains=search) |
                    Q(letter_type__name__icontains=search) |
                    Q(subject__icontains=search)
                )
            if letter_type:
                queryset = queryset.filter(letter_type=letter_type)
            if status:
                queryset = queryset.filter(status=status)
            if date_from:
                queryset = queryset.filter(issue_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(issue_date__lte=date_to)
            if created_by:
                queryset = queryset.filter(created_by=created_by)
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LetterSearchForm(self.request.GET)
        context['letter_types'] = LetterType.objects.filter(is_active=True)
        return context


class GeneratedLetterDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = GeneratedLetter
    template_name = 'hr_letters_documents/generated_letter_detail.html'
    context_object_name = 'letter'
    permission_required = 'hr_letters_documents.view_generatedletter'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all()[:10]
        context['approvals'] = self.object.approvals.all()
        return context


@login_required
@permission_required('hr_letters_documents.add_generatedletter')
def letter_create(request):
    """Create a new letter"""
    if request.method == 'POST':
        form = LetterGenerationForm(request.POST)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.created_by = request.user
            
            # Auto-generate content from template
            template = form.cleaned_data['template']
            employee = form.cleaned_data['employee']
            
            # Replace placeholders in content
            content = template.content
            arabic_content = template.arabic_content
            
            # Common placeholders
            placeholders = {
                '{{employee_name}}': employee.full_name,
                '{{designation}}': employee.designation or 'N/A',
                '{{department}}': employee.department.name if employee.department else 'N/A',
                '{{employee_id}}': employee.employee_id or 'N/A',
                '{{date_of_joining}}': employee.date_of_joining.strftime('%B %d, %Y') if employee.date_of_joining else 'N/A',
                '{{salary}}': f"AED {employee.salary:,}" if employee.salary else 'N/A',
                '{{issue_date}}': letter.issue_date.strftime('%B %d, %Y'),
                '{{company_name}}': 'Your Company Name',  # Replace with actual company name
            }
            
            for placeholder, value in placeholders.items():
                content = content.replace(placeholder, str(value))
                arabic_content = arabic_content.replace(placeholder, str(value))
            
            letter.content = content
            letter.arabic_content = arabic_content
            letter.save()
            
            # Create history entry
            LetterHistory.objects.create(
                letter=letter,
                action='created',
                user=request.user,
                details=f'Letter created by {request.user.get_full_name()}'
            )
            
            messages.success(request, 'Letter created successfully.')
            return redirect('hr_letters_documents:letter_detail', pk=letter.pk)
    else:
        form = LetterGenerationForm()
    
    return render(request, 'hr_letters_documents/generated_letter_form.html', {'form': form})


@login_required
@permission_required('hr_letters_documents.change_generatedletter')
def letter_edit(request, pk):
    """Edit an existing letter"""
    letter = get_object_or_404(GeneratedLetter, pk=pk)
    
    if request.method == 'POST':
        form = LetterEditForm(request.POST, instance=letter)
        if form.is_valid():
            letter = form.save()
            
            # Create history entry
            LetterHistory.objects.create(
                letter=letter,
                action='updated',
                user=request.user,
                details=f'Letter updated by {request.user.get_full_name()}'
            )
            
            messages.success(request, 'Letter updated successfully.')
            return redirect('hr_letters_documents:letter_detail', pk=letter.pk)
    else:
        form = LetterEditForm(instance=letter)
    
    return render(request, 'hr_letters_documents/generated_letter_form.html', {
        'form': form, 'letter': letter, 'is_edit': True
    })


@login_required
@permission_required('hr_letters_documents.change_generatedletter')
def letter_finalize(request, pk):
    """Finalize a letter"""
    letter = get_object_or_404(GeneratedLetter, pk=pk)
    
    if letter.status != 'draft':
        messages.error(request, 'Only draft letters can be finalized.')
        return redirect('hr_letters_documents:letter_detail', pk=letter.pk)
    
    letter.status = 'finalized'
    letter.finalized_by = request.user
    letter.finalized_at = timezone.now()
    letter.save()
    
    # Create history entry
    LetterHistory.objects.create(
        letter=letter,
        action='finalized',
        user=request.user,
        details=f'Letter finalized by {request.user.get_full_name()}'
    )
    
    messages.success(request, 'Letter finalized successfully.')
    return redirect('hr_letters_documents:letter_detail', pk=letter.pk)


@login_required
@permission_required('hr_letters_documents.change_generatedletter')
def letter_sign(request, pk):
    """Sign a letter"""
    letter = get_object_or_404(GeneratedLetter, pk=pk)
    
    if letter.status != 'finalized':
        messages.error(request, 'Only finalized letters can be signed.')
        return redirect('hr_letters_documents:letter_detail', pk=letter.pk)
    
    letter.status = 'signed'
    letter.signed_by = request.user
    letter.signed_at = timezone.now()
    letter.save()
    
    # Create history entry
    LetterHistory.objects.create(
        letter=letter,
        action='signed',
        user=request.user,
        details=f'Letter signed by {request.user.get_full_name()}'
    )
    
    messages.success(request, 'Letter signed successfully.')
    return redirect('hr_letters_documents:letter_detail', pk=letter.pk)


@login_required
@permission_required('hr_letters_documents.delete_generatedletter')
def letter_delete(request, pk):
    """Delete a letter"""
    letter = get_object_or_404(GeneratedLetter, pk=pk)
    
    if request.method == 'POST':
        letter.delete()
        messages.success(request, 'Letter deleted successfully.')
        return redirect('hr_letters_documents:letter_list')
    
    return render(request, 'hr_letters_documents/generated_letter_confirm_delete.html', {
        'letter': letter
    })


# Document Management Views
class DocumentCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = DocumentCategory
    template_name = 'hr_letters_documents/document_category_list.html'
    context_object_name = 'categories'
    permission_required = 'hr_letters_documents.view_documentcategory'


class DocumentCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DocumentCategory
    form_class = DocumentCategoryForm
    template_name = 'hr_letters_documents/document_category_form.html'
    permission_required = 'hr_letters_documents.add_documentcategory'
    success_url = reverse_lazy('hr_letters_documents:document_category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Document category created successfully.')
        return super().form_valid(form)


class DocumentCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = DocumentCategory
    form_class = DocumentCategoryForm
    template_name = 'hr_letters_documents/document_category_form.html'
    permission_required = 'hr_letters_documents.change_documentcategory'
    success_url = reverse_lazy('hr_letters_documents:document_category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Document category updated successfully.')
        return super().form_valid(form)


class DocumentCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = DocumentCategory
    template_name = 'hr_letters_documents/document_category_confirm_delete.html'
    permission_required = 'hr_letters_documents.delete_documentcategory'
    success_url = reverse_lazy('hr_letters_documents:document_category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Document category deleted successfully.')
        return super().delete(request, *args, **kwargs)


class HRDocumentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = HRDocument
    template_name = 'hr_letters_documents/hr_document_list.html'
    context_object_name = 'documents'
    permission_required = 'hr_letters_documents.view_hrdocument'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = HRDocument.objects.select_related('category', 'uploaded_by').all().order_by('-uploaded_at')
        
        form = DocumentSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            category = form.cleaned_data.get('category')
            is_public = form.cleaned_data.get('is_public')
            uploaded_by = form.cleaned_data.get('uploaded_by')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )
            if category:
                queryset = queryset.filter(category=category)
            if is_public:
                queryset = queryset.filter(is_public=(is_public == 'True'))
            if uploaded_by:
                queryset = queryset.filter(uploaded_by=uploaded_by)
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DocumentSearchForm(self.request.GET)
        context['document_categories'] = DocumentCategory.objects.filter(is_active=True)
        return context


class HRDocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = HRDocument
    form_class = HRDocumentForm
    template_name = 'hr_letters_documents/hr_document_form.html'
    permission_required = 'hr_letters_documents.add_hrdocument'
    success_url = reverse_lazy('hr_letters_documents:hr_document_list')
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        if form.instance.file:
            form.instance.file_type = os.path.splitext(form.instance.file.name)[1]
            form.instance.file_size = form.instance.file.size
        messages.success(self.request, 'Document uploaded successfully.')
        return super().form_valid(form)


class HRDocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = HRDocument
    form_class = HRDocumentForm
    template_name = 'hr_letters_documents/hr_document_form.html'
    permission_required = 'hr_letters_documents.change_hrdocument'
    success_url = reverse_lazy('hr_letters_documents:hr_document_list')
    
    def form_valid(self, form):
        if form.instance.file:
            form.instance.file_type = os.path.splitext(form.instance.file.name)[1]
            form.instance.file_size = form.instance.file.size
        messages.success(self.request, 'Document updated successfully.')
        return super().form_valid(form)


class HRDocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = HRDocument
    template_name = 'hr_letters_documents/hr_document_confirm_delete.html'
    permission_required = 'hr_letters_documents.delete_hrdocument'
    success_url = reverse_lazy('hr_letters_documents:hr_document_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Document deleted successfully.')
        return super().delete(request, *args, **kwargs)


# AJAX Views
@login_required
@require_http_methods(["GET"])
def get_templates_for_letter_type(request):
    """Get templates for a specific letter type"""
    letter_type_id = request.GET.get('letter_type_id')
    if letter_type_id:
        templates = LetterTemplate.objects.filter(
            letter_type_id=letter_type_id,
            is_active=True
        ).values('id', 'title', 'language')
        return JsonResponse({'templates': list(templates)})
    return JsonResponse({'templates': []})


@login_required
@require_http_methods(["GET"])
def get_employee_details(request):
    """Get employee details for letter generation"""
    employee_id = request.GET.get('employee_id')
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            data = {
                'full_name': employee.full_name,
                'designation': employee.designation or 'N/A',
                'department': employee.department.name if employee.department else 'N/A',
                'employee_id': employee.employee_id or 'N/A',
                'date_of_joining': employee.date_of_joining.strftime('%B %d, %Y') if employee.date_of_joining else 'N/A',
                'salary': f"AED {employee.salary:,}" if employee.salary else 'N/A',
            }
            return JsonResponse(data)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
    return JsonResponse({'error': 'Employee ID required'}, status=400)


@login_required
@require_http_methods(["POST"])
def preview_letter(request):
    """Preview letter content"""
    template_id = request.POST.get('template_id')
    employee_id = request.POST.get('employee_id')
    
    if template_id and employee_id:
        try:
            template = LetterTemplate.objects.get(id=template_id)
            employee = Employee.objects.get(id=employee_id)
            
            # Replace placeholders
            content = template.content
            arabic_content = template.arabic_content
            
            placeholders = {
                '{{employee_name}}': employee.full_name,
                '{{designation}}': employee.designation or 'N/A',
                '{{department}}': employee.department.name if employee.department else 'N/A',
                '{{employee_id}}': employee.employee_id or 'N/A',
                '{{date_of_joining}}': employee.date_of_joining.strftime('%B %d, %Y') if employee.date_of_joining else 'N/A',
                '{{salary}}': f"AED {employee.salary:,}" if employee.salary else 'N/A',
                '{{issue_date}}': timezone.now().strftime('%B %d, %Y'),
                '{{company_name}}': 'Your Company Name',
            }
            
            for placeholder, value in placeholders.items():
                content = content.replace(placeholder, str(value))
                arabic_content = arabic_content.replace(placeholder, str(value))
            
            return JsonResponse({
                'content': content,
                'arabic_content': arabic_content,
                'subject': template.subject
            })
        except (LetterTemplate.DoesNotExist, Employee.DoesNotExist):
            return JsonResponse({'error': 'Template or employee not found'}, status=404)
    
    return JsonResponse({'error': 'Template ID and Employee ID required'}, status=400)


@login_required
@require_http_methods(["GET"])
def get_template_details(request):
    """AJAX endpoint to get template details"""
    template_id = request.GET.get('template_id')
    
    if not template_id:
        return JsonResponse({'success': False, 'message': 'Template ID required'})
    
    try:
        template = LetterTemplate.objects.get(id=template_id)
        return JsonResponse({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.title,
                'english_subject': template.subject,
                'english_content': template.content,
                'arabic_subject': '',  # Not available in current model
                'arabic_content': template.arabic_content,
                'description': template.title,
            }
        })
    except LetterTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Template not found'})


@login_required
@permission_required('hr_letters_documents.add_generatedletter')
def bulk_letter_generation(request):
    """Generate multiple letters at once"""
    if request.method == 'POST':
        # Handle AJAX request for auto-save
        if request.POST.get('auto_save'):
            return JsonResponse({'success': True, 'message': 'Auto-saved successfully'})
        
        # Get form data
        letter_type_id = request.POST.get('letter_type')
        template_id = request.POST.get('template')
        employee_ids = request.POST.getlist('employees')
        english_subject = request.POST.get('english_subject')
        english_content = request.POST.get('english_content')
        arabic_subject = request.POST.get('arabic_subject')
        arabic_content = request.POST.get('arabic_content')
        issue_date = request.POST.get('issue_date')
        effective_date = request.POST.get('effective_date')
        notes = request.POST.get('notes')
        
        if not letter_type_id or not template_id or not employee_ids:
            return JsonResponse({
                'success': False, 
                'message': 'Letter type, template, and at least one employee are required'
            })
        
        try:
            letter_type = LetterType.objects.get(id=letter_type_id)
            template = LetterTemplate.objects.get(id=template_id)
            employees = Employee.objects.filter(id__in=employee_ids, status='active')
            
            if not employees.exists():
                return JsonResponse({
                    'success': False, 
                    'message': 'No valid employees found'
                })
            
            created_letters = []
            for employee in employees:
                # Create letter for each employee
                letter = GeneratedLetter.objects.create(
                    letter_type=letter_type,
                    template=template,
                    employee=employee,
                    subject=english_subject,
                    content=english_content,
                    arabic_content=arabic_content,
                    issue_date=issue_date or timezone.now().date(),
                    effective_date=effective_date,
                    notes=notes,
                    status='draft',
                    created_by=request.user
                )
                
                # Generate content with placeholders
                content = english_content or template.content or ''
                arabic_content_text = arabic_content or template.arabic_content or ''
                
                placeholders = {
                    '{{employee_name}}': f"{employee.first_name} {employee.last_name}",
                    '{{designation}}': employee.designation or 'N/A',
                    '{{department}}': employee.department.name if employee.department else 'N/A',
                    '{{employee_id}}': employee.employee_id or 'N/A',
                    '{{date_of_joining}}': employee.date_of_joining.strftime('%B %d, %Y') if employee.date_of_joining else 'N/A',
                    '{{salary}}': f"AED {employee.salary:,}" if employee.salary else 'N/A',
                    '{{issue_date}}': (issue_date or timezone.now().date()).strftime('%B %d, %Y'),
                    '{{company_name}}': 'Your Company Name',
                }
                
                for placeholder, value in placeholders.items():
                    content = content.replace(placeholder, str(value))
                    arabic_content_text = arabic_content_text.replace(placeholder, str(value))
                
                letter.content = content
                letter.arabic_content = arabic_content_text
                letter.save()
                
                created_letters.append(letter)
                
                # Create history entry
                LetterHistory.objects.create(
                    letter=letter,
                    action='created',
                    user=request.user,
                    details=f'Letter created via bulk generation'
                )
            
            return JsonResponse({
                'success': True,
                'generated_count': len(created_letters),
                'message': f'{len(created_letters)} letters created successfully'
            })
            
        except (LetterType.DoesNotExist, LetterTemplate.DoesNotExist):
            return JsonResponse({
                'success': False, 
                'message': 'Invalid letter type or template'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error creating letters: {str(e)}'
            })
    
    # GET request - show the form
    context = {
        'letter_types': LetterType.objects.filter(is_active=True),
        'employees': Employee.objects.filter(status='active').order_by('first_name', 'last_name'),
        'total_employees': Employee.objects.filter(status='active').count(),
        'total_letter_types': LetterType.objects.filter(is_active=True).count(),
        'today_date': timezone.now().date(),
    }
    
    return render(request, 'hr_letters_documents/bulk_letter_generation.html', context)
