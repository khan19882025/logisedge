import json
import csv
import io
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    EmailTemplate, EmailCampaign, RecipientList, Recipient, 
    EmailTracking, EmailQueue, EmailSettings
)
from .forms import (
    EmailTemplateForm, EmailCampaignForm, RecipientListForm, 
    EmailSettingsForm, CampaignPreviewForm, CampaignFilterForm,
    RecipientUploadForm
)


@login_required
@permission_required('bulk_email_sender.view_emailcampaign')
def dashboard(request):
    """Main dashboard for bulk email sender"""
    
    # Get campaign statistics
    total_campaigns = EmailCampaign.objects.count()
    active_campaigns = EmailCampaign.objects.filter(
        status__in=['scheduled', 'queued', 'sending']
    ).count()
    completed_campaigns = EmailCampaign.objects.filter(status='completed').count()
    failed_campaigns = EmailCampaign.objects.filter(status='failed').count()
    
    # Get recent campaigns
    recent_campaigns = EmailCampaign.objects.order_by('-created_at')[:5]
    
    # Get campaign performance data
    campaign_stats = EmailCampaign.objects.filter(status='completed').aggregate(
        total_sent=Count('recipients', filter=Q(recipients__status='sent')),
        total_delivered=Count('recipients', filter=Q(recipients__status='delivered'))
    )
    
    # Get recent activity
    recent_activity = EmailTracking.objects.select_related(
        'recipient__campaign', 'recipient'
    ).order_by('-timestamp')[:10]
    
    # Get template statistics
    total_templates = EmailTemplate.objects.count()
    active_templates = EmailTemplate.objects.filter(is_active=True).count()
    
    # Get recipient list statistics
    total_lists = RecipientList.objects.count()
    
    context = {
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'completed_campaigns': completed_campaigns,
        'failed_campaigns': failed_campaigns,
        'recent_campaigns': recent_campaigns,
        'campaign_stats': campaign_stats,
        'recent_activity': recent_activity,
        'total_templates': total_templates,
        'active_templates': active_templates,
        'total_lists': total_lists,
    }
    
    return render(request, 'bulk_email_sender/dashboard.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailtemplate')
def template_list(request):
    """List all email templates"""
    
    templates = EmailTemplate.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by template type
    template_type = request.GET.get('type', '')
    if template_type:
        templates = templates.filter(template_type=template_type)
    
    # Filter by status
    is_active = request.GET.get('active', '')
    if is_active != '':
        templates = templates.filter(is_active=is_active == 'true')
    
    # Pagination
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'template_type': template_type,
        'is_active': is_active,
        'template_types': EmailTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'bulk_email_sender/template_list.html', context)


@login_required
@permission_required('bulk_email_sender.add_emailtemplate')
def template_create(request):
    """Create a new email template"""
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            
            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect('bulk_email_sender:template_detail', pk=template.pk)
    else:
        form = EmailTemplateForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'template_types': EmailTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'bulk_email_sender/template_form.html', context)


@login_required
@permission_required('bulk_email_sender.change_emailtemplate')
def template_edit(request, pk):
    """Edit an existing email template"""
    
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save(commit=False)
            template.version += 1
            template.save()
            
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('bulk_email_sender:template_detail', pk=template.pk)
    else:
        form = EmailTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'action': 'Edit',
        'template_types': EmailTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'bulk_email_sender/template_form.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailtemplate')
def template_detail(request, pk):
    """View template details"""
    
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    # Get campaigns using this template
    campaigns = template.campaigns.all().order_by('-created_at')[:10]
    
    # Get placeholder variables
    placeholders = template.get_placeholder_list()
    
    context = {
        'template': template,
        'campaigns': campaigns,
        'placeholders': placeholders,
    }
    
    return render(request, 'bulk_email_sender/template_detail.html', context)


@login_required
@permission_required('bulk_email_sender.delete_emailtemplate')
def template_delete(request, pk):
    """Delete an email template"""
    
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect('bulk_email_sender:template_list')
    
    context = {
        'template': template,
    }
    
    return render(request, 'bulk_email_sender/template_confirm_delete.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailcampaign')
def campaign_list(request):
    """List all email campaigns"""
    
    campaigns = EmailCampaign.objects.select_related('template').all().order_by('-created_at')
    
    # Apply filters
    filter_form = CampaignFilterForm(request.GET)
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        template = filter_form.cleaned_data.get('template')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if search:
            campaigns = campaigns.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if status:
            campaigns = campaigns.filter(status=status)
        
        if priority:
            campaigns = campaigns.filter(priority=priority)
        
        if template:
            campaigns = campaigns.filter(template=template)
        
        if date_from:
            campaigns = campaigns.filter(created_at__date__gte=date_from)
        
        if date_to:
            campaigns = campaigns.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(campaigns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'campaign_statuses': EmailCampaign.CAMPAIGN_STATUS,
        'campaign_priorities': EmailCampaign.PRIORITY_LEVELS,
    }
    
    return render(request, 'bulk_email_sender/campaign_list.html', context)


@login_required
@permission_required('bulk_email_sender.add_emailcampaign')
def campaign_create(request):
    """Create a new email campaign"""
    
    if request.method == 'POST':
        form = EmailCampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            
            # Handle scheduling
            schedule_type = form.cleaned_data.get('schedule_type')
            if schedule_type == 'send_now':
                campaign.status = 'queued'
            elif schedule_type == 'schedule_later':
                campaign.status = 'scheduled'
            else:  # draft
                campaign.status = 'draft'
            
            campaign.save()
            
            messages.success(request, f'Campaign "{campaign.name}" created successfully!')
            return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)
    else:
        form = EmailCampaignForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'campaign_statuses': EmailCampaign.CAMPAIGN_STATUS,
        'campaign_priorities': EmailCampaign.PRIORITY_LEVELS,
    }
    
    return render(request, 'bulk_email_sender/campaign_form.html', context)


@login_required
@permission_required('bulk_email_sender.change_emailcampaign')
def campaign_edit(request, pk):
    """Edit an existing email campaign"""
    
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    
    if request.method == 'POST':
        form = EmailCampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, f'Campaign "{campaign.name}" updated successfully!')
            return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)
    else:
        form = EmailCampaignForm(instance=campaign)
    
    context = {
        'form': form,
        'campaign': campaign,
        'action': 'Edit',
        'campaign_statuses': EmailCampaign.CAMPAIGN_STATUS,
        'campaign_priorities': EmailCampaign.PRIORITY_LEVELS,
    }
    
    return render(request, 'bulk_email_sender/campaign_form.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailcampaign')
def campaign_detail(request, pk):
    """View campaign details"""
    
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    
    # Get campaign statistics
    recipients = campaign.recipients.all()
    total_recipients = recipients.count()
    sent_count = recipients.filter(status='sent').count()
    delivered_count = recipients.filter(status='delivered').count()
    opened_count = recipients.filter(status='opened').count()
    clicked_count = recipients.filter(status='clicked').count()
    failed_count = recipients.filter(status='failed').count()
    bounced_count = recipients.filter(status='bounced').count()
    
    # Calculate rates
    delivery_rate = (delivered_count / total_recipients * 100) if total_recipients > 0 else 0
    open_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0
    click_rate = (clicked_count / sent_count * 100) if sent_count > 0 else 0
    
    # Get recent activity
    recent_activity = EmailTracking.objects.filter(
        recipient__campaign=campaign
    ).select_related('recipient').order_by('-timestamp')[:20]
    
    # Get queue information
    queues = campaign.queues.all().order_by('batch_number')
    
    context = {
        'campaign': campaign,
        'total_recipients': total_recipients,
        'sent_count': sent_count,
        'delivered_count': delivered_count,
        'opened_count': opened_count,
        'clicked_count': clicked_count,
        'failed_count': failed_count,
        'bounced_count': bounced_count,
        'delivery_rate': delivery_rate,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'recent_activity': recent_activity,
        'queues': queues,
    }
    
    return render(request, 'bulk_email_sender/campaign_detail.html', context)


@login_required
@permission_required('bulk_email_sender.change_emailcampaign')
def campaign_preview(request, pk):
    """Preview campaign with test data"""
    
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    
    if request.method == 'POST':
        form = CampaignPreviewForm(request.POST)
        if form.is_valid():
            test_email = form.cleaned_data['test_email']
            test_data = form.cleaned_data.get('test_data', '{}')
            preview_type = form.cleaned_data['preview_type']
            
            try:
                test_data_dict = json.loads(test_data) if test_data else {}
            except json.JSONDecodeError:
                messages.error(request, 'Invalid JSON format for test data')
                form = CampaignPreviewForm(request.POST)
                context = {'form': form, 'campaign': campaign}
                return render(request, 'bulk_email_sender/campaign_preview.html', context)
            
            # Render template with test data
            html_content = campaign.template.html_content
            text_content = campaign.template.plain_text_content
            
            # Replace placeholders with test data
            for key, value in test_data_dict.items():
                placeholder = f'{{{{{key}}}}}'
                html_content = html_content.replace(placeholder, str(value))
                text_content = text_content.replace(placeholder, str(value))
            
            context = {
                'campaign': campaign,
                'form': form,
                'html_content': html_content,
                'text_content': text_content,
                'preview_type': preview_type,
                'test_data': test_data_dict,
            }
            
            return render(request, 'bulk_email_sender/campaign_preview.html', context)
    else:
        form = CampaignPreviewForm()
    
    context = {
        'form': form,
        'campaign': campaign,
    }
    
    return render(request, 'bulk_email_sender/campaign_preview.html', context)


@login_required
@permission_required('bulk_email_sender.change_emailcampaign')
def campaign_start(request, pk):
    """Start a campaign"""
    
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    
    if request.method == 'POST':
        if campaign.status == 'draft':
            # Check if campaign has recipients
            if campaign.recipients.count() == 0:
                messages.error(request, 'Cannot start campaign without recipients')
                return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)
            
            campaign.status = 'queued'
            campaign.started_at = timezone.now()
            campaign.save()
            
            # TODO: Add Celery task to start sending emails
            # start_campaign_sending.delay(campaign.pk)
            
            messages.success(request, f'Campaign "{campaign.name}" started successfully!')
        else:
            messages.warning(request, f'Campaign "{campaign.name}" cannot be started in its current status')
    
    return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)


@login_required
@permission_required('bulk_email_sender.change_emailcampaign')
def campaign_pause(request, pk):
    """Pause a campaign"""
    
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    
    if request.method == 'POST':
        if campaign.status in ['queued', 'sending']:
            campaign.status = 'paused'
            campaign.save()
            
            messages.success(request, f'Campaign "{campaign.name}" paused successfully!')
        else:
            messages.warning(request, f'Campaign "{campaign.name}" cannot be paused in its current status')
    
    return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)


@login_required
@permission_required('bulk_email_sender.change_emailcampaign')
def campaign_cancel(request, pk):
    """Cancel a campaign"""
    
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    
    if request.method == 'POST':
        if campaign.status in ['draft', 'scheduled', 'queued', 'sending', 'paused']:
            campaign.status = 'cancelled'
            campaign.save()
            
            messages.success(request, f'Campaign "{campaign.name}" cancelled successfully!')
        else:
            messages.warning(request, f'Campaign "{campaign.name}" cannot be cancelled in its current status')
    
    return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)


@login_required
@permission_required('bulk_email_sender.view_recipientlist')
def recipient_list_list(request):
    """List all recipient lists"""
    
    lists = RecipientList.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        lists = lists.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by list type
    list_type = request.GET.get('type', '')
    if list_type:
        lists = lists.filter(list_type=list_type)
    
    # Pagination
    paginator = Paginator(lists, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'list_type': list_type,
        'list_types': RecipientList.LIST_TYPES,
    }
    
    return render(request, 'bulk_email_sender/recipient_list_list.html', context)


@login_required
@permission_required('bulk_email_sender.add_recipientlist')
def recipient_list_create(request):
    """Create a new recipient list"""
    
    if request.method == 'POST':
        form = RecipientListForm(request.POST, request.FILES)
        if form.is_valid():
            recipient_list = form.save(commit=False)
            recipient_list.created_by = request.user
            recipient_list.save()
            
            # Handle file upload if present
            if form.cleaned_data.get('file_upload'):
                # TODO: Process uploaded file and create recipients
                pass
            
            messages.success(request, f'Recipient list "{recipient_list.name}" created successfully!')
            return redirect('bulk_email_sender:recipient_list_detail', pk=recipient_list.pk)
    else:
        form = RecipientListForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'list_types': RecipientList.LIST_TYPES,
    }
    
    return render(request, 'bulk_email_sender/recipient_list_form.html', context)


@login_required
@permission_required('bulk_email_sender.view_recipientlist')
def recipient_list_detail(request, pk):
    """View recipient list details"""
    
    recipient_list = get_object_or_404(RecipientList, pk=pk)
    
    # Get recipients in this list
    recipients = recipient_list.recipients.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(recipients, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'recipient_list': recipient_list,
        'page_obj': page_obj,
    }
    
    return render(request, 'bulk_email_sender/recipient_list_detail.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailsettings')
def settings_list(request):
    """List all email settings configurations"""
    
    settings_list = EmailSettings.objects.all().order_by('-created_at')
    
    context = {
        'settings_list': settings_list,
    }
    
    return render(request, 'bulk_email_sender/settings_list.html', context)


@login_required
@permission_required('bulk_email_sender.add_emailsettings')
def settings_create(request):
    """Create new email settings configuration"""
    
    if request.method == 'POST':
        form = EmailSettingsForm(request.POST)
        if form.is_valid():
            email_settings = form.save(commit=False)
            email_settings.created_by = request.user
            email_settings.save()
            
            messages.success(request, f'Email settings "{email_settings.name}" created successfully!')
            return redirect('bulk_email_sender:settings_detail', pk=email_settings.pk)
    else:
        form = EmailSettingsForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'provider_choices': EmailSettings.PROVIDER_CHOICES,
    }
    
    return render(request, 'bulk_email_sender/settings_form.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailsettings')
def settings_detail(request, pk):
    """View email settings details"""
    
    email_settings = get_object_or_404(EmailSettings, pk=pk)
    
    context = {
        'email_settings': email_settings,
    }
    
    return render(request, 'bulk_email_sender/settings_detail.html', context)


@login_required
@permission_required('bulk_email_sender.view_emailtracking')
def tracking_dashboard(request):
    """Email tracking and analytics dashboard"""
    
    # Get tracking statistics
    total_opens = EmailTracking.objects.filter(tracking_type='open').count()
    total_clicks = EmailTracking.objects.filter(tracking_type='click').count()
    total_bounces = EmailTracking.objects.filter(tracking_type='bounce').count()
    total_unsubscribes = EmailTracking.objects.filter(tracking_type='unsubscribe').count()
    
    # Get recent tracking events
    recent_events = EmailTracking.objects.select_related(
        'recipient__campaign', 'recipient'
    ).order_by('-timestamp')[:50]
    
    # Get campaign performance
    campaign_performance = EmailCampaign.objects.filter(
        status='completed'
    ).annotate(
        open_count=Count('recipients__tracking_events', filter=Q(recipients__tracking_events__tracking_type='open')),
        click_count=Count('recipients__tracking_events', filter=Q(recipients__tracking_events__tracking_type='click'))
    ).order_by('-created_at')[:10]
    
    context = {
        'total_opens': total_opens,
        'total_clicks': total_clicks,
        'total_bounces': total_bounces,
        'total_unsubscribes': total_unsubscribes,
        'recent_events': recent_events,
        'campaign_performance': campaign_performance,
    }
    
    return render(request, 'bulk_email_sender/tracking_dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def tracking_webhook(request):
    """Webhook endpoint for email tracking events"""
    
    try:
        data = json.loads(request.body)
        
        # Extract tracking information
        tracking_type = data.get('type')
        recipient_email = data.get('email')
        campaign_id = data.get('campaign_id')
        timestamp = data.get('timestamp')
        
        if not all([tracking_type, recipient_email, campaign_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Find recipient
        try:
            recipient = Recipient.objects.get(
                email=recipient_email,
                campaign_id=campaign_id
            )
        except Recipient.DoesNotExist:
            return JsonResponse({'error': 'Recipient not found'}, status=404)
        
        # Create tracking event
        tracking_data = {
            'recipient': recipient,
            'tracking_type': tracking_type,
            'timestamp': datetime.fromisoformat(timestamp) if timestamp else timezone.now(),
        }
        
        # Add type-specific data
        if tracking_type == 'click':
            tracking_data['clicked_url'] = data.get('url', '')
            tracking_data['link_text'] = data.get('link_text', '')
        elif tracking_type == 'bounce':
            tracking_data['bounce_type'] = data.get('bounce_type', '')
            tracking_data['bounce_reason'] = data.get('bounce_reason', '')
        
        # Add IP and user agent if available
        if 'ip_address' in data:
            tracking_data['ip_address'] = data['ip_address']
        if 'user_agent' in data:
            tracking_data['user_agent'] = data['user_agent']
        
        EmailTracking.objects.create(**tracking_data)
        
        # Update recipient status if needed
        if tracking_type == 'open' and recipient.status == 'delivered':
            recipient.status = 'opened'
            recipient.opened_at = timezone.now()
            recipient.save()
        elif tracking_type == 'click' and recipient.status in ['delivered', 'opened']:
            recipient.status = 'clicked'
            recipient.clicked_at = timezone.now()
            recipient.save()
        elif tracking_type == 'bounce':
            recipient.status = 'bounced'
            recipient.save()
        elif tracking_type == 'unsubscribe':
            recipient.status = 'unsubscribed'
            recipient.is_unsubscribed = True
            recipient.unsubscribe_date = timezone.now()
            recipient.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required('bulk_email_sender.add_recipient')
def recipient_upload(request):
    """Upload recipients via CSV/Excel file"""
    
    if request.method == 'POST':
        form = RecipientUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            has_headers = form.cleaned_data['has_headers']
            email_column = form.cleaned_data['email_column']
            first_name_column = form.cleaned_data.get('first_name_column')
            last_name_column = form.cleaned_data.get('last_name_column')
            
            try:
                # Process the uploaded file
                if file.name.endswith('.csv'):
                    # Handle CSV file
                    decoded_file = file.read().decode('utf-8')
                    csv_reader = csv.DictReader(io.StringIO(decoded_file))
                    
                    # Validate columns exist
                    if email_column not in csv_reader.fieldnames:
                        raise ValidationError(f"Column '{email_column}' not found in CSV file")
                    
                    # Process rows
                    recipients_data = []
                    for row in csv_reader:
                        recipient_data = {
                            'email': row[email_column].strip(),
                        }
                        
                        if first_name_column and first_name_column in row:
                            recipient_data['first_name'] = row[first_name_column].strip()
                        
                        if last_name_column and last_name_column in row:
                            recipient_data['last_name'] = row[last_name_column].strip()
                        
                        recipients_data.append(recipient_data)
                    
                    messages.success(request, f'Successfully processed {len(recipients_data)} recipients from CSV file')
                    
                else:
                    # Handle Excel file
                    # TODO: Implement Excel processing
                    messages.error(request, 'Excel file processing not yet implemented')
                    return redirect('bulk_email_sender:recipient_upload')
                
                # Store processed data in session for confirmation
                request.session['uploaded_recipients'] = recipients_data
                return redirect('bulk_email_sender:recipient_upload_confirm')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    
    else:
        form = RecipientUploadForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'bulk_email_sender/recipient_upload.html', context)


@login_required
@permission_required('bulk_email_sender.add_recipient')
def recipient_upload_confirm(request):
    """Confirm and save uploaded recipients"""
    
    recipients_data = request.session.get('uploaded_recipients', [])
    
    if not recipients_data:
        messages.error(request, 'No recipient data found. Please upload a file first.')
        return redirect('bulk_email_sender:recipient_upload')
    
    if request.method == 'POST':
        # Get campaign and list information
        campaign_id = request.POST.get('campaign_id')
        list_id = request.POST.get('list_id')
        
        if not campaign_id:
            messages.error(request, 'Campaign selection is required')
            return redirect('bulk_email_sender:recipient_upload_confirm')
        
        try:
            campaign = EmailCampaign.objects.get(pk=campaign_id)
            
            with transaction.atomic():
                # Create recipients
                created_count = 0
                for recipient_data in recipients_data:
                    # Check if recipient already exists
                    if not Recipient.objects.filter(
                        campaign=campaign,
                        email=recipient_data['email']
                    ).exists():
                        Recipient.objects.create(
                            campaign=campaign,
                            **recipient_data
                        )
                        created_count += 1
                
                messages.success(request, f'Successfully created {created_count} new recipients')
                
                # Clear session data
                del request.session['uploaded_recipients']
                
                return redirect('bulk_email_sender:campaign_detail', pk=campaign.pk)
                
        except EmailCampaign.DoesNotExist:
            messages.error(request, 'Selected campaign not found')
        except Exception as e:
            messages.error(request, f'Error creating recipients: {str(e)}')
    
    # Get available campaigns and lists
    campaigns = EmailCampaign.objects.filter(status='draft')
    recipient_lists = RecipientList.objects.all()
    
    context = {
        'recipients_data': recipients_data,
        'campaigns': campaigns,
        'recipient_lists': recipient_lists,
    }
    
    return render(request, 'bulk_email_sender/recipient_upload_confirm.html', context)
