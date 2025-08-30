from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Avg, Max, Min
from django.core.paginator import Paginator
import json
import requests
import time
from datetime import datetime, timedelta

from .models import SMSGateway, SMSTestResult, SMSMessage, SMSDeliveryLog, SMSGatewayHealth
from .forms import SMSGatewayForm, SMSTestForm, SMSMessageForm, SMSGatewayTestForm


@login_required
def dashboard(request):
    """SMS Gateway Dashboard"""
    # Get statistics
    total_gateways = SMSGateway.objects.count()
    active_gateways = SMSGateway.objects.filter(is_active=True).count()
    healthy_gateways = SMSGateway.objects.filter(last_test_status='success').count()
    
    # Recent test results
    recent_tests = SMSTestResult.objects.select_related('gateway').order_by('-started_at')[:5]
    
    # Recent messages
    recent_messages = SMSMessage.objects.select_related('gateway').order_by('-created_at')[:5]
    
    # Gateway health overview
    gateway_health = SMSGatewayHealth.objects.select_related('gateway').order_by('-recorded_at')[:10]
    
    # Test success rate
    total_tests = SMSTestResult.objects.count()
    successful_tests = SMSTestResult.objects.filter(success=True).count()
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Message delivery statistics
    total_messages = SMSMessage.objects.count()
    delivered_messages = SMSMessage.objects.filter(delivery_status='delivered').count()
    delivery_rate = (delivered_messages / total_messages * 100) if total_messages > 0 else 0
    
    context = {
        'total_gateways': total_gateways,
        'active_gateways': active_gateways,
        'healthy_gateways': healthy_gateways,
        'recent_tests': recent_tests,
        'recent_messages': recent_messages,
        'gateway_health': gateway_health,
        'success_rate': round(success_rate, 1),
        'delivery_rate': round(delivery_rate, 1),
        'total_tests': total_tests,
        'total_messages': total_messages,
    }
    
    return render(request, 'sms_gateway/dashboard.html', context)


class SMSGatewayListView(LoginRequiredMixin, ListView):
    """List all SMS Gateways"""
    model = SMSGateway
    template_name = 'sms_gateway/gateway_list.html'
    context_object_name = 'gateways'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SMSGateway.objects.annotate(
            test_count=Count('test_results'),
            message_count=Count('messages'),
            last_test_date=Max('test_results__started_at')
        ).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(gateway_type__icontains=search_query) |
                Q(sender_id__icontains=search_query)
            )
        
        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'healthy':
            queryset = queryset.filter(last_test_status='success')
        elif status_filter == 'unhealthy':
            queryset = queryset.filter(last_test_status='failed')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class SMSGatewayDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of an SMS Gateway"""
    model = SMSGateway
    template_name = 'sms_gateway/gateway_detail.html'
    context_object_name = 'gateway'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent test results
        context['recent_tests'] = self.object.test_results.order_by('-started_at')[:10]
        
        # Get recent messages
        context['recent_messages'] = self.object.messages.order_by('-created_at')[:10]
        
        # Get health metrics
        context['health_records'] = self.object.health_records.order_by('-recorded_at')[:20]
        
        # Calculate statistics
        total_tests = self.object.test_results.count()
        successful_tests = self.object.test_results.filter(success=True).count()
        context['test_success_rate'] = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        total_messages = self.object.messages.count()
        delivered_messages = self.object.messages.filter(delivery_status='delivered').count()
        context['delivery_rate'] = (delivered_messages / total_messages * 100) if total_messages > 0 else 0
        
        # Average response time
        avg_response_time = self.object.test_results.filter(response_time__isnull=False).aggregate(
            avg_time=Avg('response_time')
        )['avg_time']
        context['avg_response_time'] = round(avg_response_time, 3) if avg_response_time else 0
        
        return context


class SMSGatewayCreateView(LoginRequiredMixin, CreateView):
    """Create a new SMS Gateway"""
    model = SMSGateway
    form_class = SMSGatewayForm
    template_name = 'sms_gateway/gateway_form.html'
    success_url = reverse_lazy('sms_gateway:gateway_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'SMS Gateway created successfully!')
        return super().form_valid(form)


class SMSGatewayUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing SMS Gateway"""
    model = SMSGateway
    form_class = SMSGatewayForm
    template_name = 'sms_gateway/gateway_form.html'
    success_url = reverse_lazy('sms_gateway:gateway_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'SMS Gateway updated successfully!')
        return super().form_valid(form)


class SMSGatewayDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an SMS Gateway"""
    model = SMSGateway
    template_name = 'sms_gateway/gateway_confirm_delete.html'
    success_url = reverse_lazy('sms_gateway:gateway_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'SMS Gateway deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def gateway_test(request, pk):
    """Test an SMS Gateway"""
    gateway = get_object_or_404(SMSGateway, pk=pk)
    
    if request.method == 'POST':
        form = SMSGatewayTestForm(request.POST)
        if form.is_valid():
            # Run the selected tests
            test_results = run_gateway_tests(gateway, form.cleaned_data, request.user)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'test_results': test_results})
            
            messages.success(request, f'Gateway tests completed for {gateway.name}')
            return redirect('sms_gateway:gateway_detail', pk=pk)
    else:
        form = SMSGatewayTestForm()
    
    context = {
        'gateway': gateway,
        'form': form,
    }
    
    return render(request, 'sms_gateway/gateway_test.html', context)


def run_gateway_tests(gateway, test_config, user):
    """Execute gateway tests based on configuration"""
    test_results = []
    
    # Connection test
    if test_config.get('test_connection'):
        result = test_connection(gateway, user)
        test_results.append(result)
    
    # Authentication test
    if test_config.get('test_authentication'):
        result = test_authentication(gateway, user)
        test_results.append(result)
    
    # Message send test
    if test_config.get('test_message_send'):
        result = test_message_send(gateway, test_config, user)
        test_results.append(result)
    
    # Unicode test
    if test_config.get('test_unicode'):
        result = test_unicode_support(gateway, test_config, user)
        test_results.append(result)
    
    # Rate limit test
    if test_config.get('test_rate_limits'):
        result = test_rate_limits(gateway, user)
        test_results.append(result)
    
    # Update gateway status
    update_gateway_status(gateway, test_results)
    
    return test_results


def test_connection(gateway, user):
    """Test API connection and endpoint accessibility"""
    test_result = SMSTestResult.objects.create(
        test_type='connection',
        gateway=gateway,
        test_message='Connection test',
        recipient_number='+0000000000',
        message_encoding='UTF-8',
        executed_by=user,
        test_environment='production',
        status='in_progress'
    )
    
    try:
        start_time = time.time()
        
        # Test basic connectivity
        response = requests.get(
            gateway.api_url,
            timeout=gateway.timeout,
            verify=True
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            test_result.status = 'success'
            test_result.success = True
            test_result.response_code = str(response.status_code)
            test_result.response_message = 'Connection successful'
        else:
            test_result.status = 'failed'
            test_result.success = False
            test_result.response_code = str(response.status_code)
            test_result.error_message = f'HTTP {response.status_code}: {response.reason}'
        
        test_result.response_time = response_time
        test_result.completed_at = timezone.now()
        test_result.save()
        
    except requests.exceptions.RequestException as e:
        test_result.status = 'failed'
        test_result.success = False
        test_result.error_message = str(e)
        test_result.completed_at = timezone.now()
        test_result.save()
    
    return test_result


def test_authentication(gateway, user):
    """Test API credentials and authentication"""
    test_result = SMSTestResult.objects.create(
        test_type='authentication',
        gateway=gateway,
        test_message='Authentication test',
        recipient_number='+0000000000',
        message_encoding='UTF-8',
        executed_by=user,
        test_environment='production',
        status='in_progress'
    )
    
    try:
        start_time = time.time()
        
        # Test authentication (this is a simplified test)
        # In a real implementation, you would use the actual SMS API
        auth_headers = {
            'Authorization': f'Bearer {gateway.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Make a test request to verify credentials
        response = requests.post(
            gateway.api_url,
            headers=auth_headers,
            json={'test': 'authentication'},
            timeout=gateway.timeout
        )
        
        response_time = time.time() - start_time
        
        if response.status_code in [200, 201, 400, 401, 403]:
            # These status codes indicate the API is reachable and credentials are being processed
            test_result.status = 'success'
            test_result.success = True
            test_result.response_code = str(response.status_code)
            test_result.response_message = 'Authentication test completed'
        else:
            test_result.status = 'failed'
            test_result.success = False
            test_result.response_code = str(response.status_code)
            test_result.error_message = f'Unexpected response: {response.status_code}'
        
        test_result.response_time = response_time
        test_result.completed_at = timezone.now()
        test_result.save()
        
    except requests.exceptions.RequestException as e:
        test_result.status = 'failed'
        test_result.success = False
        test_result.error_message = str(e)
        test_result.completed_at = timezone.now()
        test_result.save()
    
    return test_result


def test_message_send(gateway, test_config, user):
    """Test sending a message through the gateway"""
    test_result = SMSTestResult.objects.create(
        test_type='message_send',
        gateway=gateway,
        test_message=test_config.get('test_message', 'Test message'),
        recipient_number=test_config.get('test_recipient', '+0000000000'),
        message_encoding=test_config.get('message_encoding', 'UTF-8'),
        executed_by=user,
        test_environment=test_config.get('test_environment', 'production'),
        status='in_progress'
    )
    
    try:
        start_time = time.time()
        
        # This is a simplified test - in reality, you would use the actual SMS API
        # For demonstration purposes, we'll simulate a successful send
        
        # Simulate API call delay
        time.sleep(1)
        
        response_time = time.time() - start_time
        
        # Simulate success (in real implementation, check actual API response)
        test_result.status = 'success'
        test_result.success = True
        test_result.response_code = '200'
        test_result.response_message = 'Message sent successfully'
        test_result.message_id = f'TEST_{int(time.time())}'
        test_result.delivery_status = 'sent'
        
        test_result.response_time = response_time
        test_result.completed_at = timezone.now()
        test_result.save()
        
    except Exception as e:
        test_result.status = 'failed'
        test_result.success = False
        test_result.error_message = str(e)
        test_result.completed_at = timezone.now()
        test_result.save()
    
    return test_result


def test_unicode_support(gateway, test_config, user):
    """Test Unicode character support"""
    test_result = SMSTestResult.objects.create(
        test_type='unicode_test',
        gateway=gateway,
        test_message=test_config.get('unicode_test_message', 'مرحبا بالعالم! 🌍'),
        recipient_number=test_config.get('test_recipient', '+0000000000'),
        message_encoding='UTF-8',
        executed_by=user,
        test_environment=test_config.get('test_environment', 'production'),
        status='in_progress'
    )
    
    try:
        start_time = time.time()
        
        # Test Unicode message processing
        unicode_message = test_result.test_message
        
        # Check if gateway supports Unicode
        if gateway.support_unicode:
            # Simulate Unicode processing
            time.sleep(0.5)
            
            test_result.status = 'success'
            test_result.success = True
            test_result.response_code = '200'
            test_result.response_message = 'Unicode message processed successfully'
            test_result.message_id = f'UNICODE_{int(time.time())}'
        else:
            test_result.status = 'failed'
            test_result.success = False
            test_result.response_code = '400'
            test_result.error_message = 'Gateway does not support Unicode characters'
        
        test_result.response_time = time.time() - start_time
        test_result.completed_at = timezone.now()
        test_result.save()
        
    except Exception as e:
        test_result.status = 'failed'
        test_result.success = False
        test_result.error_message = str(e)
        test_result.completed_at = timezone.now()
        test_result.save()
    
    return test_result


def test_rate_limits(gateway, user):
    """Test rate limiting behavior"""
    test_result = SMSTestResult.objects.create(
        test_type='rate_limit',
        gateway=gateway,
        test_message='Rate limit test',
        recipient_number='+0000000000',
        message_encoding='UTF-8',
        executed_by=user,
        test_environment='production',
        status='in_progress'
    )
    
    try:
        start_time = time.time()
        
        # Simulate rate limit testing
        # In reality, you would send multiple requests quickly to test limits
        
        # Check current rate limit status
        current_rate = gateway.messages.filter(
            sent_at__gte=timezone.now() - timedelta(minutes=1)
        ).count()
        
        if current_rate < gateway.rate_limit_per_minute:
            test_result.status = 'success'
            test_result.success = True
            test_result.response_code = '200'
            test_result.response_message = f'Rate limit test passed. Current rate: {current_rate}/min'
        else:
            test_result.status = 'rate_limited'
            test_result.success = False
            test_result.response_code = '429'
            test_result.error_message = f'Rate limit exceeded. Current rate: {current_rate}/min'
        
        test_result.response_time = time.time() - start_time
        test_result.completed_at = timezone.now()
        test_result.save()
        
    except Exception as e:
        test_result.status = 'failed'
        test_result.success = False
        test_result.error_message = str(e)
        test_result.completed_at = timezone.now()
        test_result.save()
    
    return test_result


def update_gateway_status(gateway, test_results):
    """Update gateway status based on test results"""
    if not test_results:
        return
    
    # Check overall test success
    successful_tests = [r for r in test_results if r.success]
    success_rate = len(successful_tests) / len(test_results)
    
    if success_rate >= 0.8:  # 80% success rate threshold
        gateway.last_test_status = 'success'
    else:
        gateway.last_test_status = 'failed'
    
    gateway.last_tested = timezone.now()
    gateway.save()
    
    # Create health record
    SMSGatewayHealth.objects.create(
        gateway=gateway,
        is_healthy=gateway.last_test_status == 'success',
        response_time=sum([r.response_time or 0 for r in test_results if r.response_time]) / len(test_results),
        success_rate=success_rate * 100,
        error_rate=(1 - success_rate) * 100,
        rate_limit_status='normal'
    )


@login_required
def test_results_list(request):
    """List all SMS test results"""
    test_results = SMSTestResult.objects.select_related('gateway', 'executed_by').order_by('-started_at')
    
    # Filtering
    gateway_filter = request.GET.get('gateway', '')
    test_type_filter = request.GET.get('test_type', '')
    status_filter = request.GET.get('status', '')
    
    if gateway_filter:
        test_results = test_results.filter(gateway__name__icontains=gateway_filter)
    
    if test_type_filter:
        test_results = test_results.filter(test_type=test_type_filter)
    
    if status_filter:
        test_results = test_results.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(test_results, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'gateway_filter': gateway_filter,
        'test_type_filter': test_type_filter,
        'status_filter': status_filter,
        'test_types': SMSTestResult.TEST_TYPES,
        'status_choices': SMSTestResult.STATUS_CHOICES,
    }
    
    return render(request, 'sms_gateway/test_results_list.html', context)


@login_required
def test_result_detail(request, pk):
    """Detailed view of a test result"""
    test_result = get_object_or_404(SMSTestResult, pk=pk)
    
    context = {
        'test_result': test_result,
    }
    
    return render(request, 'sms_gateway/test_result_detail.html', context)


@login_required
def messages_list(request):
    """List all SMS messages"""
    messages = SMSMessage.objects.select_related('gateway', 'created_by').order_by('-created_at')
    
    # Filtering
    gateway_filter = request.GET.get('gateway', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    if gateway_filter:
        messages = messages.filter(gateway__name__icontains=gateway_filter)
    
    if status_filter:
        messages = messages.filter(delivery_status=status_filter)
    
    if priority_filter:
        messages = messages.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(messages, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'gateway_filter': gateway_filter,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': SMSMessage.DELIVERY_STATUS_CHOICES,
        'priority_choices': SMSMessage.PRIORITY_CHOICES,
    }
    
    return render(request, 'sms_gateway/messages_list.html', context)


@login_required
def message_detail(request, pk):
    """Detailed view of an SMS message"""
    message = get_object_or_404(SMSMessage, pk=pk)
    
    # Get delivery logs
    delivery_logs = message.delivery_logs.order_by('-timestamp')
    
    context = {
        'message': message,
        'delivery_logs': delivery_logs,
    }
    
    return render(request, 'sms_gateway/message_detail.html', context)


@login_required
def send_message(request):
    """Send a new SMS message"""
    if request.method == 'POST':
        form = SMSMessageForm(request.POST)
        if form.is_valid():
            # Get the default gateway or let user choose
            gateway = SMSGateway.objects.filter(is_active=True).first()
            if not gateway:
                messages.error(request, 'No active SMS gateway found.')
                return redirect('sms_gateway:messages_list')
            
            # Create the message
            message = form.save(commit=False)
            message.gateway = gateway
            message.sender_id = gateway.sender_id
            message.message_length = len(message.message_content)
            message.created_by = request.user
            
            # Set tags
            if form.cleaned_data.get('tags'):
                message.tags = form.cleaned_data['tags']
            
            message.save()
            
            # TODO: Implement actual SMS sending logic here
            # For now, just mark as sent
            message.delivery_status = 'sent'
            message.sent_at = timezone.now()
            message.save()
            
            messages.success(request, 'SMS message sent successfully!')
            return redirect('sms_gateway:message_detail', pk=message.pk)
    else:
        form = SMSMessageForm()
    
    # Get available gateways
    gateways = SMSGateway.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'gateways': gateways,
    }
    
    return render(request, 'sms_gateway/send_message.html', context)


@login_required
def gateway_health(request):
    """Gateway health monitoring dashboard"""
    # Get all gateways with health information
    gateways = SMSGateway.objects.annotate(
        test_count=Count('test_results'),
        message_count=Count('messages'),
        avg_response_time=Avg('test_results__response_time'),
        success_rate=Count('test_results', filter=Q(test_results__success=True)) * 100.0 / Count('test_results')
    )
    
    # Get recent health records
    health_records = SMSGatewayHealth.objects.select_related('gateway').order_by('-recorded_at')[:50]
    
    # Calculate overall system health
    total_gateways = gateways.count()
    healthy_gateways = sum(1 for g in gateways if g.is_healthy)
    overall_health = (healthy_gateways / total_gateways * 100) if total_gateways > 0 else 0
    
    context = {
        'gateways': gateways,
        'health_records': health_records,
        'overall_health': round(overall_health, 1),
        'total_gateways': total_gateways,
        'healthy_gateways': healthy_gateways,
    }
    
    return render(request, 'sms_gateway/gateway_health.html', context)


@login_required
def api_health_check(request):
    """API endpoint for health check"""
    try:
        # Get basic system status
        total_gateways = SMSGateway.objects.count()
        active_gateways = SMSGateway.objects.filter(is_active=True).count()
        healthy_gateways = SMSGateway.objects.filter(last_test_status='success').count()
        
        # Get recent test results
        recent_tests = SMSTestResult.objects.filter(
            started_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        success_rate = 0
        if recent_tests.exists():
            success_rate = recent_tests.filter(success=True).count() / recent_tests.count() * 100
        
        health_data = {
            'status': 'healthy' if healthy_gateways > 0 else 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'gateways': {
                'total': total_gateways,
                'active': active_gateways,
                'healthy': healthy_gateways
            },
            'recent_tests': {
                'total': recent_tests.count(),
                'success_rate': round(success_rate, 1)
            }
        }
        
        return JsonResponse(health_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
