from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.mail import send_mail, get_connection
from django.conf import settings
import smtplib
import imaplib
import poplib
import ssl
import socket
import traceback
from datetime import datetime, timedelta
import json

from .models import EmailConfiguration, EmailTestResult, EmailNotification
from .forms import (
    EmailConfigurationForm, EmailTestForm, EmailNotificationForm,
    EmailConfigurationSearchForm
)


@login_required
@permission_required('email_configuration.view_emailconfiguration')
def dashboard(request):
    """Email configuration dashboard"""
    
    # Get statistics
    total_configs = EmailConfiguration.objects.count()
    active_configs = EmailConfiguration.objects.filter(is_active=True).count()
    smtp_configs = EmailConfiguration.objects.filter(protocol='smtp').count()
    imap_configs = EmailConfiguration.objects.filter(protocol='imap').count()
    pop3_configs = EmailConfiguration.objects.filter(protocol='pop3').count()
    
    # Test status statistics
    test_stats = EmailConfiguration.objects.values('last_test_status').annotate(
        count=Count('id')
    )
    
    # Recent test results
    recent_tests = EmailTestResult.objects.select_related('configuration').order_by('-started_at')[:10]
    
    # Recent notifications
    recent_notifications = EmailNotification.objects.select_related('configuration').order_by('-created_at')[:10]
    
    # Configuration health
    healthy_configs = EmailConfiguration.objects.filter(
        last_test_status='success',
        is_active=True
    ).count()
    
    problematic_configs = EmailConfiguration.objects.filter(
        last_test_status='failed',
        is_active=True
    ).count()
    
    context = {
        'total_configs': total_configs,
        'active_configs': active_configs,
        'smtp_configs': smtp_configs,
        'imap_configs': imap_configs,
        'pop3_configs': pop3_configs,
        'test_stats': test_stats,
        'recent_tests': recent_tests,
        'recent_notifications': recent_notifications,
        'healthy_configs': healthy_configs,
        'problematic_configs': problematic_configs,
    }
    
    return render(request, 'email_configuration/dashboard.html', context)


class EmailConfigurationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for email configurations"""
    model = EmailConfiguration
    template_name = 'email_configuration/configuration_list.html'
    context_object_name = 'configurations'
    permission_required = 'email_configuration.view_emailconfiguration'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EmailConfiguration.objects.select_related('created_by', 'updated_by')
        
        # Apply search filters
        form = EmailConfigurationSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            protocol = form.cleaned_data.get('protocol')
            status = form.cleaned_data.get('status')
            encryption = form.cleaned_data.get('encryption')
            created_by = form.cleaned_data.get('created_by')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if name:
                queryset = queryset.filter(name__icontains=name)
            if protocol:
                queryset = queryset.filter(protocol=protocol)
            if status:
                if status == 'active':
                    queryset = queryset.filter(is_active=True)
                elif status == 'inactive':
                    queryset = queryset.filter(is_active=False)
                elif status in ['success', 'failed', 'untested']:
                    queryset = queryset.filter(last_test_status=status)
            if encryption:
                queryset = queryset.filter(encryption=encryption)
            if created_by:
                queryset = queryset.filter(created_by__username__icontains=created_by)
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-is_default', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = EmailConfigurationSearchForm(self.request.GET)
        return context


class EmailConfigurationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for email configuration"""
    model = EmailConfiguration
    template_name = 'email_configuration/configuration_detail.html'
    context_object_name = 'configuration'
    permission_required = 'email_configuration.view_emailconfiguration'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_results'] = self.object.test_results.order_by('-started_at')[:10]
        context['notifications'] = self.object.notifications_sent.order_by('-created_at')[:10]
        return context


class EmailConfigurationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for email configuration"""
    model = EmailConfiguration
    form_class = EmailConfigurationForm
    template_name = 'email_configuration/configuration_form.html'
    permission_required = 'email_configuration.add_emailconfiguration'
    success_url = reverse_lazy('email_configuration:configuration_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Email configuration created successfully.')
        return super().form_valid(form)


class EmailConfigurationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for email configuration"""
    model = EmailConfiguration
    form_class = EmailConfigurationForm
    template_name = 'email_configuration/configuration_form.html'
    permission_required = 'email_configuration.change_emailconfiguration'
    success_url = reverse_lazy('email_configuration:configuration_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Email configuration updated successfully.')
        return super().form_valid(form)


class EmailConfigurationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for email configuration"""
    model = EmailConfiguration
    template_name = 'email_configuration/configuration_confirm_delete.html'
    permission_required = 'email_configuration.delete_emailconfiguration'
    success_url = reverse_lazy('email_configuration:configuration_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email configuration deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@permission_required('email_configuration.change_emailconfiguration')
def test_email_configuration(request, pk):
    """Test email configuration"""
    configuration = get_object_or_404(EmailConfiguration, pk=pk)
    
    if request.method == 'POST':
        form = EmailTestForm(request.POST)
        if form.is_valid():
            test_type = form.cleaned_data['test_type']
            test_email = form.cleaned_data.get('test_email')
            test_subject = form.cleaned_data.get('test_subject', 'Test Email')
            test_message = form.cleaned_data.get('test_message', 'This is a test email from the ERP system.')
            
            # Create test result record
            test_result = EmailTestResult.objects.create(
                configuration=configuration,
                test_type=test_type,
                status='pending',
                test_email=test_email or '',
                test_subject=test_subject,
                tested_by=request.user
            )
            
            try:
                if test_type == 'connection':
                    result = test_connection(configuration)
                elif test_type == 'authentication':
                    result = test_authentication(configuration)
                elif test_type == 'send_test':
                    result = test_send_email(configuration, test_email, test_subject, test_message)
                elif test_type == 'receive_test':
                    result = test_receive_email(configuration, test_email)
                elif test_type == 'full_test':
                    result = test_full_configuration(configuration, test_email, test_subject, test_message)
                else:
                    result = {'status': 'error', 'message': 'Invalid test type'}
                
                # Update test result
                test_result.status = result['status']
                test_result.test_message = result.get('message', '')
                test_result.error_details = result.get('error_details', '')
                test_result.completed_at = timezone.now()
                test_result.save()
                
                # Update configuration test status
                configuration.last_tested = timezone.now()
                configuration.last_test_status = result['status']
                configuration.last_test_message = result.get('message', '')
                configuration.save()
                
                if result['status'] == 'success':
                    messages.success(request, f'{test_type.replace("_", " ").title()} completed successfully.')
                else:
                    messages.error(request, f'{test_type.replace("_", " ").title()} failed: {result.get("message", "Unknown error")}')
                
            except Exception as e:
                test_result.status = 'error'
                test_result.test_message = f'Test failed with exception: {str(e)}'
                test_result.error_details = str(e)
                test_result.stack_trace = traceback.format_exc()
                test_result.completed_at = timezone.now()
                test_result.save()
                
                messages.error(request, f'Test failed with exception: {str(e)}')
            
            return redirect('email_configuration:configuration_detail', pk=pk)
    else:
        form = EmailTestForm()
    
    context = {
        'configuration': configuration,
        'form': form,
    }
    return render(request, 'email_configuration/test_configuration.html', context)


def test_connection(configuration):
    """Test connection to email server"""
    try:
        if configuration.protocol == 'smtp':
            return test_smtp_connection(configuration)
        elif configuration.protocol == 'imap':
            return test_imap_connection(configuration)
        elif configuration.protocol == 'pop3':
            return test_pop3_connection(configuration)
        else:
            return {'status': 'error', 'message': 'Unsupported protocol'}
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'error_details': str(e)}


def test_smtp_connection(configuration):
    """Test SMTP connection"""
    try:
        # Create SSL context
        if configuration.encryption == 'ssl':
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(configuration.host, configuration.port, timeout=configuration.timeout, context=context)
        elif configuration.encryption == 'tls':
            server = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
            server.starttls(context=ssl.create_default_context())
        elif configuration.encryption == 'starttls':
            server = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
            server.starttls(context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
        
        server.quit()
        return {'status': 'success', 'message': 'SMTP connection successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'SMTP connection failed: {str(e)}', 'error_details': str(e)}


def test_imap_connection(configuration):
    """Test IMAP connection"""
    try:
        if configuration.encryption == 'ssl':
            server = imaplib.IMAP4_SSL(configuration.host, configuration.port)
        else:
            server = imaplib.IMAP4(configuration.host, configuration.port)
        
        server.logout()
        return {'status': 'success', 'message': 'IMAP connection successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'IMAP connection failed: {str(e)}', 'error_details': str(e)}


def test_pop3_connection(configuration):
    """Test POP3 connection"""
    try:
        if configuration.encryption == 'ssl':
            server = poplib.POP3_SSL(configuration.host, configuration.port)
        else:
            server = poplib.POP3(configuration.host, configuration.port)
        
        server.quit()
        return {'status': 'success', 'message': 'POP3 connection successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'POP3 connection failed: {str(e)}', 'error_details': str(e)}


def test_authentication(configuration):
    """Test authentication with email server"""
    try:
        if configuration.protocol == 'smtp':
            return test_smtp_authentication(configuration)
        elif configuration.protocol == 'imap':
            return test_imap_authentication(configuration)
        elif configuration.protocol == 'pop3':
            return test_pop3_authentication(configuration)
        else:
            return {'status': 'error', 'message': 'Unsupported protocol'}
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'error_details': str(e)}


def test_smtp_authentication(configuration):
    """Test SMTP authentication"""
    try:
        if configuration.encryption == 'ssl':
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(configuration.host, configuration.port, timeout=configuration.timeout, context=context)
        elif configuration.encryption == 'tls':
            server = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
            server.starttls(context=ssl.create_default_context())
        elif configuration.encryption == 'starttls':
            server = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
            server.starttls(context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
        
        if configuration.use_authentication:
            server.login(configuration.username, configuration.password)
        
        server.quit()
        return {'status': 'success', 'message': 'SMTP authentication successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'SMTP authentication failed: {str(e)}', 'error_details': str(e)}


def test_imap_authentication(configuration):
    """Test IMAP authentication"""
    try:
        if configuration.encryption == 'ssl':
            server = imaplib.IMAP4_SSL(configuration.host, configuration.port)
        else:
            server = imaplib.IMAP4(configuration.host, configuration.port)
        
        if configuration.use_authentication:
            server.login(configuration.username, configuration.password)
        
        server.logout()
        return {'status': 'success', 'message': 'IMAP authentication successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'IMAP authentication failed: {str(e)}', 'error_details': str(e)}


def test_pop3_authentication(configuration):
    """Test POP3 authentication"""
    try:
        if configuration.encryption == 'ssl':
            server = poplib.POP3_SSL(configuration.host, configuration.port)
        else:
            server = poplib.POP3(configuration.host, configuration.port)
        
        if configuration.use_authentication:
            server.user(configuration.username)
            server.pass_(configuration.password)
        
        server.quit()
        return {'status': 'success', 'message': 'POP3 authentication successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'POP3 authentication failed: {str(e)}', 'error_details': str(e)}


def test_send_email(configuration, test_email, test_subject, test_message):
    """Test sending email"""
    try:
        if configuration.protocol != 'smtp':
            return {'status': 'error', 'message': 'Only SMTP configurations can send emails'}
        
        # Create connection
        if configuration.encryption == 'ssl':
            context = ssl.create_default_context()
            connection = smtplib.SMTP_SSL(configuration.host, configuration.port, timeout=configuration.timeout, context=context)
        elif configuration.encryption == 'tls':
            connection = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
            connection.starttls(context=ssl.create_default_context())
        elif configuration.encryption == 'starttls':
            connection = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
            connection.starttls(context=ssl.create_default_context())
        else:
            connection = smtplib.SMTP(configuration.host, configuration.port, timeout=configuration.timeout)
        
        # Authenticate if required
        if configuration.use_authentication:
            connection.login(configuration.username, configuration.password)
        
        # Send test email
        connection.sendmail(
            configuration.username,
            [test_email],
            f'Subject: {test_subject}\n\n{test_message}'
        )
        
        connection.quit()
        return {'status': 'success', 'message': f'Test email sent successfully to {test_email}'}
    except Exception as e:
        return {'status': 'failed', 'message': f'Failed to send test email: {str(e)}', 'error_details': str(e)}


def test_receive_email(configuration, test_email):
    """Test receiving email (IMAP/POP3)"""
    try:
        if configuration.protocol not in ['imap', 'pop3']:
            return {'status': 'error', 'message': 'Only IMAP/POP3 configurations can receive emails'}
        
        if configuration.protocol == 'imap':
            return test_imap_receive(configuration)
        else:
            return test_pop3_receive(configuration)
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'error_details': str(e)}


def test_imap_receive(configuration):
    """Test IMAP email receiving"""
    try:
        if configuration.encryption == 'ssl':
            server = imaplib.IMAP4_SSL(configuration.host, configuration.port)
        else:
            server = imaplib.IMAP4(configuration.host, configuration.port)
        
        if configuration.use_authentication:
            server.login(configuration.username, configuration.password)
        
        # List mailboxes
        server.list()
        
        server.logout()
        return {'status': 'success', 'message': 'IMAP email receiving test successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'IMAP email receiving test failed: {str(e)}', 'error_details': str(e)}


def test_pop3_receive(configuration):
    """Test POP3 email receiving"""
    try:
        if configuration.encryption == 'ssl':
            server = poplib.POP3_SSL(configuration.host, configuration.port)
        else:
            server = poplib.POP3(configuration.host, configuration.port)
        
        if configuration.use_authentication:
            server.user(configuration.username)
            server.pass_(configuration.password)
        
        # Get mailbox stats
        server.stat()
        
        server.quit()
        return {'status': 'success', 'message': 'POP3 email receiving test successful'}
    except Exception as e:
        return {'status': 'failed', 'message': f'POP3 email receiving test failed: {str(e)}', 'error_details': str(e)}


def test_full_configuration(configuration, test_email, test_subject, test_message):
    """Test full configuration (connection, auth, send/receive)"""
    results = []
    
    # Test connection
    conn_result = test_connection(configuration)
    results.append(f"Connection: {conn_result['status']}")
    if conn_result['status'] != 'success':
        return {'status': 'failed', 'message': 'Connection test failed', 'error_details': conn_result.get('error_details', '')}
    
    # Test authentication
    auth_result = test_authentication(configuration)
    results.append(f"Authentication: {auth_result['status']}")
    if auth_result['status'] != 'success':
        return {'status': 'failed', 'message': 'Authentication test failed', 'error_details': auth_result.get('error_details', '')}
    
    # Test sending (for SMTP)
    if configuration.protocol == 'smtp':
        send_result = test_send_email(configuration, test_email, test_subject, test_message)
        results.append(f"Send Test: {send_result['status']}")
        if send_result['status'] != 'success':
            return {'status': 'failed', 'message': 'Send test failed', 'error_details': send_result.get('error_details', '')}
    
    # Test receiving (for IMAP/POP3)
    if configuration.protocol in ['imap', 'pop3']:
        receive_result = test_receive_email(configuration, test_email)
        results.append(f"Receive Test: {receive_result['status']}")
        if receive_result['status'] != 'success':
            return {'status': 'failed', 'message': 'Receive test failed', 'error_details': receive_result.get('error_details', '')}
    
    return {'status': 'success', 'message': 'All tests passed: ' + ', '.join(results)}


@login_required
@permission_required('email_configuration.view_emailtestresult')
def test_results_list(request):
    """List view for email test results"""
    test_results = EmailTestResult.objects.select_related('configuration', 'tested_by').order_by('-started_at')
    
    # Pagination
    paginator = Paginator(test_results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'test_results': page_obj,
    }
    return render(request, 'email_configuration/test_results_list.html', context)


@login_required
@permission_required('email_configuration.view_emailnotification')
def notifications_list(request):
    """List view for email notifications"""
    notifications = EmailNotification.objects.select_related('configuration', 'created_by').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj,
    }
    return render(request, 'email_configuration/notifications_list.html', context)


@login_required
@permission_required('email_configuration.add_emailnotification')
def create_notification(request):
    """Create email notification"""
    if request.method == 'POST':
        form = EmailNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.created_by = request.user
            notification.save()
            
            messages.success(request, 'Email notification created successfully.')
            return redirect('email_configuration:notifications_list')
    else:
        form = EmailNotificationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'email_configuration/notification_form.html', context)


@login_required
@permission_required('email_configuration.view_emailconfiguration')
def configuration_health(request):
    """Configuration health dashboard"""
    configs = EmailConfiguration.objects.filter(is_active=True)
    
    health_data = []
    for config in configs:
        health_data.append({
            'id': config.id,
            'name': config.name,
            'protocol': config.protocol,
            'status': config.last_test_status,
            'last_tested': config.last_tested,
            'message': config.last_test_message,
        })
    
    return JsonResponse({'health_data': health_data})


@login_required
@permission_required('email_configuration.view_emailconfiguration')
def configuration_statistics(request):
    """Configuration statistics API"""
    total_configs = EmailConfiguration.objects.count()
    active_configs = EmailConfiguration.objects.filter(is_active=True).count()
    smtp_configs = EmailConfiguration.objects.filter(protocol='smtp').count()
    imap_configs = EmailConfiguration.objects.filter(protocol='imap').count()
    pop3_configs = EmailConfiguration.objects.filter(protocol='pop3').count()
    
    # Test status statistics
    test_stats = EmailConfiguration.objects.values('last_test_status').annotate(
        count=Count('id')
    )
    
    # Recent test results
    recent_tests = EmailTestResult.objects.select_related('configuration').order_by('-started_at')[:10]
    
    # Recent notifications
    recent_notifications = EmailNotification.objects.select_related('configuration').order_by('-created_at')[:10]
    
    # Configuration health
    healthy_configs = EmailConfiguration.objects.filter(
        last_test_status='success',
        is_active=True
    ).count()
    
    problematic_configs = EmailConfiguration.objects.filter(
        last_test_status='failed',
        is_active=True
    ).count()
    
    context = {
        'total_configs': total_configs,
        'active_configs': active_configs,
        'smtp_configs': smtp_configs,
        'imap_configs': imap_configs,
        'pop3_configs': pop3_configs,
        'test_stats': list(test_stats),
        'recent_tests': [
            {
                'id': test.id,
                'configuration_name': test.configuration.name,
                'status': test.status,
                'started_at': test.started_at.isoformat() if test.started_at else None,
                'duration': test.duration,
                'message': test.message
            }
            for test in recent_tests
        ],
        'recent_notifications': [
            {
                'id': notification.id,
                'name': notification.name,
                'configuration_name': notification.configuration.name,
                'created_at': notification.created_at.isoformat() if notification.created_at else None,
                'status': notification.status
            }
            for notification in recent_notifications
        ],
        'healthy_configs': healthy_configs,
        'problematic_configs': problematic_configs,
    }
    
    return JsonResponse(context)


@login_required
@permission_required('email_configuration.view_emailtestresult')
def test_result_detail(request, pk):
    """Detail view for email test result"""
    test_result = get_object_or_404(EmailTestResult, pk=pk)
    
    context = {
        'test_result': test_result,
    }
    return render(request, 'email_configuration/test_result_detail.html', context)


@login_required
@permission_required('email_configuration.view_emailnotification')
def notification_detail(request, pk):
    """Detail view for email notification"""
    notification = get_object_or_404(EmailNotification, pk=pk)
    
    context = {
        'notification': notification,
    }
    return render(request, 'email_configuration/notification_detail.html', context)


@login_required
@permission_required('email_configuration.change_emailnotification')
def notification_update(request, pk):
    """Update email notification"""
    notification = get_object_or_404(EmailNotification, pk=pk)
    
    if request.method == 'POST':
        form = EmailNotificationForm(request.POST, instance=notification)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.updated_by = request.user
            notification.save()
            
            messages.success(request, 'Email notification updated successfully.')
            return redirect('email_configuration:notification_detail', pk=notification.pk)
    else:
        form = EmailNotificationForm(instance=notification)
    
    context = {
        'form': form,
        'notification': notification,
    }
    return render(request, 'email_configuration/notification_form.html', context)


@login_required
@permission_required('email_configuration.delete_emailnotification')
def notification_delete(request, pk):
    """Delete email notification"""
    notification = get_object_or_404(EmailNotification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Email notification deleted successfully.')
        return redirect('email_configuration:notifications_list')
    
    context = {
        'notification': notification,
    }
    return render(request, 'email_configuration/notification_confirm_delete.html', context)
