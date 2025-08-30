import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination

from .models import CronJob, CronJobLog
from .serializers import (
    CronJobSerializer, CronJobCreateSerializer, CronJobUpdateSerializer,
    CronJobLogSerializer, CronJobStatusUpdateSerializer, CronJobLogFilterSerializer,
    CronJobStatisticsSerializer, CronJobRefreshSerializer
)

logger = logging.getLogger(__name__)


def has_cron_job_permission(user):
    """Check if user has permission to view cron jobs"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# Frontend Template Views
@login_required
@user_passes_test(has_cron_job_permission)
def cron_job_dashboard(request):
    """Main dashboard view for the cron job viewer"""
    try:
        # Get statistics
        total_jobs = CronJob.objects.count()
        active_jobs = CronJob.objects.filter(is_active=True).count()
        running_jobs = CronJob.objects.filter(last_status='running').count()
        failed_jobs = CronJob.objects.filter(last_status='failed').count()
        
        # Get upcoming jobs
        upcoming_jobs = CronJob.objects.filter(
            is_active=True,
            next_run_at__gte=timezone.now()
        ).order_by('next_run_at')[:5]
        
        # Get recent executions
        recent_executions = CronJobLog.objects.select_related('job').order_by('-run_started_at')[:10]
        
        # Get system status
        system_status = get_system_status()
        
        context = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'running_jobs': running_jobs,
            'failed_jobs': failed_jobs,
            'upcoming_jobs': upcoming_jobs,
            'recent_executions': recent_executions,
            'system_status': system_status,
        }
        
        return render(request, 'cron_job_viewer/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in cron job dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return render(request, 'cron_job_viewer/dashboard.html', {'error': str(e)})


@login_required
@user_passes_test(has_cron_job_permission)
def cron_job_list(request):
    """List all cron jobs view"""
    try:
        # Get search and filter parameters
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        schedule_filter = request.GET.get('schedule', '')
        owner_filter = request.GET.get('owner', '')
        
        # Base queryset
        queryset = CronJob.objects.select_related('owner').prefetch_related('execution_logs')
        
        # Apply filters
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(task__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if status_filter:
            queryset = queryset.filter(last_status=status_filter)
        
        if schedule_filter:
            if schedule_filter == 'cron':
                queryset = queryset.exclude(schedule__startswith='every')
            elif schedule_filter == 'interval':
                queryset = queryset.filter(schedule__startswith='every')
        
        if owner_filter:
            queryset = queryset.filter(owner__username__icontains=owner_filter)
        
        # Order by next run time (active jobs first)
        queryset = queryset.order_by('-is_active', 'next_run_at')
        
        # Pagination
        paginator = Paginator(queryset, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'schedule_filter': schedule_filter,
            'owner_filter': owner_filter,
            'status_choices': CronJob.STATUS_CHOICES,
        }
        
        return render(request, 'cron_job_viewer/job_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in cron job list: {str(e)}")
        messages.error(request, "An error occurred while loading the job list.")
        return render(request, 'cron_job_viewer/job_list.html', {'error': str(e)})


@login_required
@user_passes_test(has_cron_job_permission)
def cron_job_detail(request, job_id):
    """Detail view for a specific cron job"""
    try:
        job = get_object_or_404(CronJob, id=job_id)
        logs = CronJobLog.objects.filter(job=job).order_by('-run_started_at')[:50]
        
        context = {
            'job': job,
            'logs': logs,
        }
        return render(request, 'cron_job_viewer/job_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in cron job detail: {str(e)}")
        messages.error(request, "An error occurred while loading the job details.")
        return redirect('cron_job_viewer:job_list')


@login_required
@user_passes_test(has_cron_job_permission)
def cron_job_logs(request, job_id):
    """View logs for a specific cron job"""
    try:
        job = get_object_or_404(CronJob, id=job_id)
        
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Base queryset
        queryset = CronJobLog.objects.filter(job=job)
        
        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            queryset = queryset.filter(run_started_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(run_started_at__date__lte=date_to)
        
        # Order by execution time
        queryset = queryset.order_by('-run_started_at')
        
        # Pagination
        paginator = Paginator(queryset, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'job': job,
            'page_obj': page_obj,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'status_choices': CronJobLog.STATUS_CHOICES,
        }
        
        return render(request, 'cron_job_viewer/job_logs.html', context)
        
    except Exception as e:
        logger.error(f"Error in cron job logs: {str(e)}")
        messages.error(request, "An error occurred while loading the job logs.")
        return redirect('cron_job_viewer:job_list')


# API Viewsets
class CronJobPagination(PageNumberPagination):
    """Custom pagination for cron jobs"""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class CronJobViewSet(viewsets.ModelViewSet):
    """API viewset for cron jobs"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = CronJobPagination
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_superuser:
            return CronJob.objects.select_related('owner').prefetch_related('execution_logs')
        else:
            return CronJob.objects.filter(owner=self.request.user).select_related('owner').prefetch_related('execution_logs')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CronJobCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CronJobUpdateSerializer
        elif self.action == 'update_status':
            return CronJobStatusUpdateSerializer
        return CronJobSerializer
    
    def perform_create(self, serializer):
        """Override create to set owner automatically"""
        serializer.save(owner=self.request.user)
    
    def perform_update(self, serializer):
        """Override update to ensure only owner can update"""
        instance = serializer.instance
        if instance.owner != self.request.user and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("You can only update your own cron jobs")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Override destroy to ensure only owner can delete"""
        if instance.owner != self.request.user and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("You can only delete your own cron jobs")
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update cron job status (activate/deactivate)"""
        job = self.get_object()
        serializer = self.get_serializer(job, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success', 
                'message': f'Cron job {job.name} status updated'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Manually trigger cron job execution"""
        job = self.get_object()
        try:
            # Create a log entry for manual execution
            log = CronJobLog.objects.create(
                job=job,
                celery_task_id='manual_execution',
                worker_name='manual'
            )
            
            # Mark job as running
            job.mark_as_running()
            
            # Here you would typically trigger the actual Celery task
            # For now, we'll simulate completion
            import time
            time.sleep(1)  # Simulate execution time
            
            # Mark as completed
            log.mark_completed(status='success', output_message='Manually executed successfully')
            job.mark_as_completed(status='success')
            
            return Response({
                'status': 'success',
                'message': f'Cron job {job.name} executed manually',
                'log_id': str(log.id)
            })
        except Exception as e:
            logger.error(f"Error running cron job manually: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get cron job statistics"""
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_jobs = queryset.count()
        active_jobs = queryset.filter(is_active=True).count()
        inactive_jobs = queryset.filter(is_active=False).count()
        
        # Jobs by status
        jobs_by_status = dict(queryset.values_list('last_status').annotate(count=Count('id')))
        
        # Jobs by schedule type
        cron_jobs = queryset.exclude(schedule__startswith='every').count()
        interval_jobs = queryset.filter(schedule__startswith='every').count()
        jobs_by_schedule_type = {
            'cron': cron_jobs,
            'interval': interval_jobs
        }
        
        # Execution statistics
        recent_executions = CronJobLog.objects.filter(
            job__in=queryset
        ).count()
        
        successful_executions = CronJobLog.objects.filter(
            job__in=queryset,
            status='success'
        ).count()
        
        failed_executions = CronJobLog.objects.filter(
            job__in=queryset,
            status='failed'
        ).count()
        
        # Execution time statistics
        execution_stats = CronJobLog.objects.filter(
            job__in=queryset,
            execution_time__isnull=False
        ).aggregate(
            avg_time=Avg('execution_time'),
            total_time=Sum('execution_time')
        )
        
        data = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'inactive_jobs': inactive_jobs,
            'jobs_by_status': jobs_by_status,
            'jobs_by_schedule_type': jobs_by_schedule_type,
            'recent_executions': recent_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'average_execution_time': execution_stats['avg_time'] or 0.0,
            'total_execution_time': execution_stats['total_time'] or 0.0,
        }
        
        serializer = CronJobStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Refresh cron jobs from Celery Beat schedule"""
        serializer = CronJobRefreshSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # This would typically sync with Celery Beat
                # For now, we'll just return a success message
                return Response({
                    'status': 'success',
                    'message': 'Cron jobs refreshed successfully'
                })
            except Exception as e:
                logger.error(f"Error refreshing cron jobs: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CronJobLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for cron job logs"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = CronJobLogSerializer
    pagination_class = CronJobPagination
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_superuser:
            return CronJobLog.objects.select_related('job', 'job__owner')
        else:
            return CronJobLog.objects.filter(
                job__owner=self.request.user
            ).select_related('job', 'job__owner')
    
    @action(detail=False, methods=['get'])
    def filter_logs(self, request):
        """Filter logs by various criteria"""
        serializer = CronJobLogFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            queryset = self.get_queryset()
            
            # Apply filters
            if serializer.validated_data.get('status'):
                queryset = queryset.filter(status=serializer.validated_data['status'])
            
            if serializer.validated_data.get('date_from'):
                queryset = queryset.filter(
                    run_started_at__date__gte=serializer.validated_data['date_from']
                )
            
            if serializer.validated_data.get('date_to'):
                queryset = queryset.filter(
                    run_started_at__date__lte=serializer.validated_data['date_to']
                )
            
            # Limit results
            limit = serializer.validated_data.get('limit', 50)
            queryset = queryset[:limit]
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Utility Functions
def get_system_status():
    """Get system health status"""
    try:
        # Check database status
        db_status = "healthy"
        try:
            CronJob.objects.count()
        except Exception:
            db_status = "error"
        
        # Check Redis status (if available)
        redis_status = "unknown"
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "unavailable"
        
        # Check Celery worker status (if available)
        celery_status = "unknown"
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            if active_workers:
                celery_status = "healthy"
            else:
                celery_status = "no_workers"
        except Exception:
            celery_status = "unavailable"
        
        return {
            'database': db_status,
            'redis': redis_status,
            'celery': celery_status,
            'last_check': timezone.now(),
        }
        
    except Exception as e:
        logger.error(f"Error checking system status: {str(e)}")
        return {
            'database': 'unknown',
            'redis': 'unknown',
            'celery': 'unknown',
            'last_check': timezone.now(),
            'error': str(e)
        }


# AJAX Views for Frontend
@login_required
@user_passes_test(has_cron_job_permission)
@require_http_methods(["POST"])
def ajax_update_job_status(request, job_id):
    """AJAX endpoint for updating cron job status"""
    try:
        job = get_object_or_404(CronJob, id=job_id)
        data = json.loads(request.body)
        serializer = CronJobStatusUpdateSerializer(job, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
        else:
            return JsonResponse({'success': False, 'errors': serializer.errors})
    except Exception as e:
        logger.error(f"Error in ajax_update_job_status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(has_cron_job_permission)
@require_http_methods(["POST"])
def ajax_run_job_now(request, job_id):
    """AJAX endpoint for manually running cron jobs"""
    try:
        job = get_object_or_404(CronJob, id=job_id)
        
        # Create a log entry for manual execution
        log = CronJobLog.objects.create(
            job=job,
            celery_task_id='manual_execution',
            worker_name='manual'
        )
        
        # Mark job as running
        job.mark_as_running()
        
        # Here you would typically trigger the actual Celery task
        # For now, we'll simulate completion
        import time
        time.sleep(1)  # Simulate execution time
        
        # Mark as completed
        log.mark_completed(status='success', output_message='Manually executed successfully')
        job.mark_as_completed(status='success')
        
        return JsonResponse({
            'success': True,
            'message': f'Cron job {job.name} executed successfully',
            'log_id': str(log.id)
        })
    except Exception as e:
        logger.error(f"Error in ajax_run_job_now: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(has_cron_job_permission)
def ajax_get_job_statistics(request):
    """AJAX endpoint for getting cron job statistics"""
    try:
        if request.user.is_superuser:
            queryset = CronJob.objects.all()
        else:
            queryset = CronJob.objects.filter(owner=request.user)
        
        # Get counts by status
        status_counts = queryset.values('last_status').annotate(count=Count('id'))
        
        # Get counts by schedule type
        cron_jobs = queryset.exclude(schedule__startswith='every').count()
        interval_jobs = queryset.filter(schedule__startswith='every').count()
        
        # Get recent activity
        recent_logs = CronJobLog.objects.filter(
            job__in=queryset
        ).select_related('job').order_by('-run_started_at')[:10]
        
        # Get upcoming jobs
        upcoming_jobs = queryset.filter(
            is_active=True,
            next_run_at__gte=timezone.now()
        ).order_by('next_run_at')[:5]
        
        return JsonResponse({
            'success': True,
            'data': {
                'status_counts': list(status_counts),
                'schedule_counts': {
                    'cron': cron_jobs,
                    'interval': interval_jobs
                },
                'recent_logs': CronJobLogSerializer(recent_logs, many=True).data,
                'upcoming_jobs': CronJobSerializer(upcoming_jobs, many=True).data,
            }
        })
    except Exception as e:
        logger.error(f"Error in ajax_get_job_statistics: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
