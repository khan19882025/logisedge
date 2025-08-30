import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    NotificationTemplate, TemplateCategory, TemplatePlaceholder,
    TemplateTest, TemplateAuditLog, TemplateVersion
)
from .forms import (
    NotificationTemplateForm, TemplateCategoryForm, TemplateTestForm,
    TemplateSearchForm, TemplateImportForm, TemplateExportForm
)

logger = logging.getLogger(__name__)


# Dashboard and Overview Views
@login_required
def dashboard(request):
    """Main dashboard for notification templates"""
    # Get statistics
    total_templates = NotificationTemplate.objects.count()
    active_templates = NotificationTemplate.objects.filter(is_active=True).count()
    pending_approval = NotificationTemplate.objects.filter(
        requires_approval=True, is_approved=False
    ).count()
    
    # Template type distribution
    template_types = NotificationTemplate.objects.values('template_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Category distribution
    categories = TemplateCategory.objects.annotate(
        template_count=Count('templates')
    ).order_by('-template_count')[:10]
    
    # Recent templates
    recent_templates = NotificationTemplate.objects.select_related(
        'category', 'created_by'
    ).order_by('-created_at')[:5]
    
    # Recent activity
    recent_activity = TemplateAuditLog.objects.select_related(
        'template', 'user'
    ).order_by('-timestamp')[:10]
    
    # Language distribution
    languages = NotificationTemplate.objects.values('language').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_templates': total_templates,
        'active_templates': active_templates,
        'pending_approval': pending_approval,
        'template_types': template_types,
        'categories': categories,
        'recent_templates': recent_templates,
        'recent_activity': recent_activity,
        'languages': languages,
    }
    
    return render(request, 'notification_templates/dashboard.html', context)


# Template Management Views
@login_required
@permission_required('notification_templates.add_notificationtemplate', raise_exception=True)
def template_list(request):
    """List all notification templates with search and filtering"""
    search_form = TemplateSearchForm(request.GET)
    templates = NotificationTemplate.objects.select_related('category', 'created_by')
    
    if search_form.is_valid():
        # Apply search filters
        search_query = search_form.cleaned_data.get('search_query')
        search_field = search_form.cleaned_data.get('search_field')
        template_type = search_form.cleaned_data.get('template_type')
        category = search_form.cleaned_data.get('category')
        language = search_form.cleaned_data.get('language')
        status = search_form.cleaned_data.get('status')
        tags = search_form.cleaned_data.get('tags')
        created_after = search_form.cleaned_data.get('created_after')
        created_before = search_form.cleaned_data.get('created_before')
        sort_by = search_form.cleaned_data.get('sort_by', '-updated_at')
        
        # Apply search query
        if search_query and search_field:
            if search_field == 'name':
                templates = templates.filter(name__icontains=search_query)
            elif search_field == 'content':
                templates = templates.filter(content__icontains=search_query)
            elif search_field == 'subject':
                templates = templates.filter(subject__icontains=search_query)
            elif search_field == 'description':
                templates = templates.filter(description__icontains=search_query)
        
        # Apply filters
        if template_type:
            templates = templates.filter(template_type=template_type)
        if category:
            templates = templates.filter(category=category)
        if language:
            templates = templates.filter(language=language)
        if status:
            if status == 'active':
                templates = templates.filter(is_active=True)
            elif status == 'inactive':
                templates = templates.filter(is_active=False)
            elif status == 'pending_approval':
                templates = templates.filter(requires_approval=True, is_approved=False)
            elif status == 'approved':
                templates = templates.filter(is_approved=True)
        
        # Apply date filters
        if created_after:
            templates = templates.filter(created_at__gte=created_after)
        if created_before:
            templates = templates.filter(created_at__lte=created_before)
        
        # Apply tags filter
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            templates = templates.filter(tags__overlap=tag_list)
        
        # Apply sorting
        if sort_by and sort_by.strip():
            templates = templates.order_by(sort_by)
        else:
            templates = templates.order_by('-updated_at')
    
    # Pagination
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': templates.count(),
    }
    
    return render(request, 'notification_templates/template_list.html', context)


@login_required
@permission_required('notification_templates.add_notificationtemplate', raise_exception=True)
def template_create(request):
    """Create a new notification template"""
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.updated_by = request.user
            
            # Handle tags
            tags = form.cleaned_data.get('tags')
            if isinstance(tags, str):
                template.tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            template.save()
            
            # Create audit log
            TemplateAuditLog.objects.create(
                template=template,
                action='created',
                user=request.user,
                change_reason=form.cleaned_data.get('change_reason', '')
            )
            
            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect('notification_templates:template_detail', pk=template.pk)
    else:
        form = NotificationTemplateForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'available_placeholders': TemplatePlaceholder.objects.filter(is_active=True)
    }
    
    return render(request, 'notification_templates/template_form.html', context)


@login_required
def template_detail(request, pk):
    """View template details"""
    template = get_object_or_404(NotificationTemplate, pk=pk)
    
    # Get versions
    versions = template.versions.order_by('-version_number')
    
    # Get tests
    tests = template.tests.order_by('-tested_at')
    
    # Get audit logs
    audit_logs = template.audit_logs.order_by('-timestamp')
    
    # Get translations
    translations = template.translations.all()
    
    context = {
        'template': template,
        'versions': versions,
        'tests': tests,
        'audit_logs': audit_logs,
        'translations': translations,
    }
    
    return render(request, 'notification_templates/template_detail.html', context)


@login_required
@permission_required('notification_templates.change_notificationtemplate', raise_exception=True)
def template_edit(request, pk):
    """Edit an existing template"""
    template = get_object_or_404(NotificationTemplate, pk=pk)
    
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            old_values = {
                'content': template.content,
                'html_content': template.html_content,
                'subject': template.subject,
            }
            
            template = form.save(commit=False)
            template.updated_by = request.user
            
            # Handle tags
            tags = form.cleaned_data.get('tags')
            if isinstance(tags, str):
                template.tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            template.save()
            
            # Create audit log
            TemplateAuditLog.objects.create(
                template=template,
                action='updated',
                user=request.user,
                old_values=old_values,
                new_values={
                    'content': template.content,
                    'html_content': template.html_content,
                    'subject': template.subject,
                },
                change_reason=form.cleaned_data.get('change_reason', '')
            )
            
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('notification_templates:template_detail', pk=template.pk)
    else:
        form = NotificationTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'action': 'Edit',
        'available_placeholders': TemplatePlaceholder.objects.filter(is_active=True)
    }
    
    return render(request, 'notification_templates/template_form.html', context)


@login_required
@permission_required('notification_templates.delete_notificationtemplate', raise_exception=True)
def template_delete(request, pk):
    """Delete a template"""
    template = get_object_or_404(NotificationTemplate, pk=pk)
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect('notification_templates:template_list')
    
    context = {
        'template': template
    }
    
    return render(request, 'notification_templates/template_confirm_delete.html', context)


# Template Testing Views
@login_required
@permission_required('notification_templates.add_templatetest', raise_exception=True)
def template_test(request, pk):
    """Test a template with sample data"""
    template = get_object_or_404(NotificationTemplate, pk=pk)
    
    if request.method == 'POST':
        form = TemplateTestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.template = template
            test.tested_by = request.user
            test.test_data = form.cleaned_data.get('test_data', {})
            test.save()
            
            # Send test notification
            try:
                if template.template_type == 'email':
                    send_test_email(template, test)
                elif template.template_type == 'sms':
                    send_test_sms(template, test)
                elif template.template_type == 'whatsapp':
                    send_test_whatsapp(template, test)
                
                test.status = 'sent'
                test.sent_at = timezone.now()
                test.save()
                
                messages.success(request, 'Test notification sent successfully!')
            except Exception as e:
                test.status = 'failed'
                test.error_message = str(e)
                test.save()
                
                messages.error(request, f'Failed to send test notification: {str(e)}')
            
            return redirect('notification_templates:template_detail', pk=template.pk)
    else:
        form = TemplateTestForm()
    
    # Generate sample test data
    sample_data = generate_sample_data(template)
    
    context = {
        'template': template,
        'form': form,
        'sample_data': sample_data,
    }
    
    return render(request, 'notification_templates/template_test.html', context)


@login_required
def template_preview(request, pk):
    """Preview template with sample data"""
    template = get_object_or_404(NotificationTemplate, pk=pk)
    
    if request.method == 'POST':
        test_data = json.loads(request.POST.get('test_data', '{}'))
    else:
        test_data = generate_sample_data(template)
    
    # Render template with test data
    preview_content = render_template_with_data(template, test_data)
    
    context = {
        'template': template,
        'preview_content': preview_content,
        'test_data': test_data,
    }
    
    return render(request, 'notification_templates/template_preview.html', context)


# Category Management Views
@login_required
@permission_required('notification_templates.add_templatecategory', raise_exception=True)
def category_list(request):
    """List all template categories"""
    categories = TemplateCategory.objects.annotate(
        template_count=Count('templates')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'notification_templates/category_list.html', context)


@login_required
@permission_required('notification_templates.add_templatecategory', raise_exception=True)
def category_create(request):
    """Create a new template category"""
    if request.method == 'POST':
        form = TemplateCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('notification_templates:category_list')
    else:
        form = TemplateCategoryForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'notification_templates/category_form.html', context)


@login_required
@permission_required('notification_templates.change_templatecategory', raise_exception=True)
def category_edit(request, pk):
    """Edit an existing category"""
    category = get_object_or_404(TemplateCategory, pk=pk)
    
    if request.method == 'POST':
        form = TemplateCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('notification_templates:category_list')
    else:
        form = TemplateCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'action': 'Edit',
    }
    
    return render(request, 'notification_templates/category_form.html', context)


# Import/Export Views
@login_required
@permission_required('notification_templates.add_notificationtemplate', raise_exception=True)
def template_import(request):
    """Import templates from external sources"""
    if request.method == 'POST':
        form = TemplateImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle import logic here
            messages.success(request, 'Templates imported successfully!')
            return redirect('notification_templates:template_list')
    else:
        form = TemplateImportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'notification_templates/template_import.html', context)


@login_required
@permission_required('notification_templates.view_notificationtemplate', raise_exception=True)
def template_export(request):
    """Export templates to external formats"""
    if request.method == 'POST':
        form = TemplateExportForm(request.POST)
        if form.is_valid():
            # Handle export logic here
            messages.success(request, 'Templates exported successfully!')
            return redirect('notification_templates:template_list')
    else:
        form = TemplateExportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'notification_templates/template_export.html', context)


# API Views for AJAX
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def get_placeholders(request):
    """Get available placeholders for templates"""
    template_type = request.POST.get('template_type')
    category = request.POST.get('category')
    
    placeholders = TemplatePlaceholder.objects.filter(is_active=True)
    
    if template_type:
        placeholders = placeholders.filter(placeholder_type__in=get_placeholder_types(template_type))
    
    if category:
        # Filter by category-specific placeholders if needed
        pass
    
    data = [{
        'name': p.name,
        'display_name': p.display_name,
        'description': p.description,
        'example_value': p.example_value,
    } for p in placeholders]
    
    return JsonResponse({'placeholders': data})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def validate_template(request):
    """Validate template content and placeholders"""
    template_type = request.POST.get('template_type')
    content = request.POST.get('content')
    html_content = request.POST.get('html_content', '')
    
    errors = []
    
    # Basic validation
    if template_type == 'email' and not html_content:
        errors.append("Email templates must have HTML content")
    
    if template_type == 'sms' and len(content) > 160:
        errors.append("SMS content cannot exceed 160 characters")
    
    if template_type == 'whatsapp' and len(content) > 1000:
        errors.append("WhatsApp content cannot exceed 1000 characters")
    
    # Placeholder validation
    import re
    placeholder_pattern = r'\{\{([^}]+)\}\}'
    found_placeholders = re.findall(placeholder_pattern, content)
    if html_content:
        found_placeholders.extend(re.findall(placeholder_pattern, html_content))
    
    found_placeholders = list(set(found_placeholders))
    
    # Check if placeholders exist in system
    available_placeholders = TemplatePlaceholder.objects.filter(
        name__in=found_placeholders, is_active=True
    ).values_list('name', flat=True)
    
    missing_placeholders = [p for p in found_placeholders if p not in available_placeholders]
    if missing_placeholders:
        errors.append(f"Unknown placeholders: {', '.join(missing_placeholders)}")
    
    return JsonResponse({
        'valid': len(errors) == 0,
        'errors': errors,
        'placeholders': found_placeholders,
        'available_placeholders': list(available_placeholders)
    })


# Helper Functions
def generate_sample_data(template):
    """Generate sample data for template testing"""
    sample_data = {}
    
    for placeholder in template.placeholders:
        if 'customer' in placeholder.lower():
            sample_data[placeholder] = 'John Doe'
        elif 'order' in placeholder.lower():
            sample_data[placeholder] = 'ORD-2024-001'
        elif 'payment' in placeholder.lower():
            sample_data[placeholder] = '$99.99'
        elif 'date' in placeholder.lower():
            sample_data[placeholder] = '2024-12-25'
        elif 'email' in placeholder.lower():
            sample_data[placeholder] = 'customer@example.com'
        elif 'phone' in placeholder.lower():
            sample_data[placeholder] = '+1234567890'
        else:
            sample_data[placeholder] = f'Sample {placeholder}'
    
    return sample_data


def render_template_with_data(template, data):
    """Render template content with provided data"""
    content = template.content
    html_content = template.html_content
    
    for placeholder, value in data.items():
        placeholder_pattern = f'{{{{{placeholder}}}}}'
        content = content.replace(placeholder_pattern, str(value))
        if html_content:
            html_content = html_content.replace(placeholder_pattern, str(value))
    
    return {
        'content': content,
        'html_content': html_content,
        'subject': template.subject
    }


def get_placeholder_types(template_type):
    """Get relevant placeholder types for template type"""
    if template_type == 'email':
        return ['customer', 'order', 'payment', 'system', 'custom']
    elif template_type == 'sms':
        return ['customer', 'order', 'payment', 'system']
    elif template_type == 'whatsapp':
        return ['customer', 'order', 'payment', 'system']
    elif template_type == 'in_app':
        return ['customer', 'order', 'payment', 'system', 'custom']
    return []


def send_test_email(template, test):
    """Send test email"""
    # This would integrate with your email system
    subject = template.subject
    html_message = template.html_content
    plain_message = strip_tags(template.content)
    
    # Replace placeholders with test data
    for placeholder, value in test.test_data.items():
        placeholder_pattern = f'{{{{{placeholder}}}}}'
        subject = subject.replace(placeholder_pattern, str(value))
        html_message = html_message.replace(placeholder_pattern, str(value))
        plain_message = plain_message.replace(placeholder_pattern, str(value))
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test.recipient_email],
        html_message=html_message,
        fail_silently=False,
    )


def send_test_sms(template, test):
    """Send test SMS"""
    # This would integrate with your SMS gateway
    content = template.content
    
    # Replace placeholders with test data
    for placeholder, value in test.test_data.items():
        placeholder_pattern = f'{{{{{placeholder}}}}}'
        content = content.replace(placeholder_pattern, str(value))
    
    # Placeholder for SMS sending logic
    logger.info(f"Would send SMS to {test.recipient_phone}: {content}")


def send_test_whatsapp(template, test):
    """Send test WhatsApp message"""
    # This would integrate with your WhatsApp API
    content = template.content
    
    # Replace placeholders with test data
    for placeholder, value in test.test_data.items():
        placeholder_pattern = f'{{{{{placeholder}}}}}'
        content = content.replace(placeholder_pattern, str(value))
    
    # Placeholder for WhatsApp sending logic
    logger.info(f"Would send WhatsApp to {test.recipient_phone}: {content}")
