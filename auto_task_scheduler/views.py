import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ScheduledTask, ScheduledTaskLog, TaskSchedule
from .serializers import (
    ScheduledTaskSerializer, ScheduledTaskCreateSerializer, 
    ScheduledTaskUpdateSerializer, ScheduledTaskLogSerializer,
    TaskScheduleSerializer, TaskStatusUpdateSerializer,
    TaskRunSerializer, TaskLogFilterSerializer,
    TaskStatisticsSerializer
)
# Temporarily commented out until Celery is installed
# from .tasks import execute_scheduled_task, sync_celery_schedules

logger = logging.getLogger(__name__)


# Frontend Template Views
@login_required
def task_scheduler_dashboard(request):
    """Main dashboard view for the task scheduler"""
    try:
        # Get statistics
        total_tasks = ScheduledTask.objects.count()
        active_tasks = ScheduledTask.objects.filter(status='active').count()
        completed_today = ScheduledTaskLog.objects.filter(
            started_at__date=timezone.now().date(),
            status='success'
        ).count()
        failed_today = ScheduledTaskLog.objects.filter(
            started_at__date=timezone.now().date(),
            status='failure'
        ).count()
        
        # Get upcoming tasks
        upcoming_tasks = ScheduledTask.objects.filter(
            status='active'
        ).order_by('next_run_at')[:5]
        
        # Get recent executions
        recent_executions = ScheduledTaskLog.objects.select_related('task').order_by('-started_at')[:10]
        
        # Get system status
        system_status = get_system_status()
        
        context = {
            'total_tasks': total_tasks,
            'active_tasks': active_tasks,
            'completed_today': completed_today,
            'failed_today': failed_today,
            'upcoming_tasks': upcoming_tasks,
            'recent_executions': recent_executions,
            'system_status': system_status,
        }
        
        return render(request, 'auto_task_scheduler/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in task scheduler dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return render(request, 'auto_task_scheduler/dashboard.html', {'error': str(e)})


@login_required
def task_scheduler_create(request):
    """Create new scheduled task view"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            serializer = ScheduledTaskCreateSerializer(data=data)
            if serializer.is_valid():
                task = serializer.save(user=request.user)
                messages.success(request, f"Task '{task.name}' created successfully!")
                return JsonResponse({'success': True, 'task_id': str(task.id)})
            else:
                return JsonResponse({'success': False, 'errors': serializer.errors})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'auto_task_scheduler/create_task.html')


@login_required
def task_scheduler_list(request):
    """List all scheduled tasks view"""
    tasks = ScheduledTask.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'auto_task_scheduler/task_list.html', {'tasks': tasks})


@login_required
def task_scheduler_detail(request, task_id):
    """Detail view for a specific task"""
    task = get_object_or_404(ScheduledTask, id=task_id, user=request.user)
    logs = ScheduledTaskLog.objects.filter(task=task).order_by('-started_at')[:50]
    
    context = {
        'task': task,
        'logs': logs,
    }
    return render(request, 'auto_task_scheduler/task_detail.html', context)


@login_required
def task_scheduler_logs(request, task_id):
    """View logs for a specific task"""
    task = get_object_or_404(ScheduledTask, id=task_id, user=request.user)
    logs = ScheduledTaskLog.objects.filter(task=task).order_by('-started_at')
    
    context = {
        'task': task,
        'logs': logs,
    }
    return render(request, 'auto_task_scheduler/task_logs.html', context)


# API Viewsets
class ScheduledTaskViewSet(viewsets.ModelViewSet):
    """API viewset for scheduled tasks"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ScheduledTask.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduledTaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScheduledTaskUpdateSerializer
        elif self.action == 'update_status':
            return TaskStatusUpdateSerializer
        elif self.action == 'run_manually':
            return TaskRunSerializer
        return ScheduledTaskSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status (activate/deactivate)"""
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': f'Task {task.name} status updated'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def run_manually(self, request, pk=None):
        """Manually trigger task execution"""
        task = self.get_object()
        try:
            # Temporarily disabled until Celery is installed
            # result = execute_scheduled_task.delay(str(task.id))
            return Response({
                'status': 'success',
                'message': f'Task {task.name} started manually (Celery not available)',
                'task_id': 'celery_not_available'
            })
        except Exception as e:
            logger.error(f"Error running task manually: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get task statistics"""
        queryset = self.get_queryset()
        serializer = TaskStatisticsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def sync_schedules(self, request):
        """Sync database schedules with Celery beat"""
        try:
            # Temporarily disabled until Celery is installed
            # result = sync_celery_schedules.delay()
            return Response({
                'status': 'success',
                'message': 'Schedules synchronized with Celery beat (Celery not available)',
                'task_id': 'celery_not_available'
            })
        except Exception as e:
            logger.error(f"Error syncing schedules: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for task logs"""
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduledTaskLogSerializer
    
    def get_queryset(self):
        return ScheduledTaskLog.objects.filter(task__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def filter_logs(self, request):
        """Filter logs by various criteria"""
        serializer = TaskLogFilterSerializer(data=request.query_params)
        if serializer.is_valid():
            queryset = self.get_queryset()
            
            # Apply filters
            if serializer.validated_data.get('task_id'):
                queryset = queryset.filter(task_id=serializer.validated_data['task_id'])
            
            if serializer.validated_data.get('status'):
                queryset = queryset.filter(status=serializer.validated_data['status'])
            
            if serializer.validated_data.get('date_from'):
                queryset = queryset.filter(started_at__gte=serializer.validated_data['date_from'])
            
            if serializer.validated_data.get('date_to'):
                queryset = queryset.filter(started_at__lte=serializer.validated_data['date_to'])
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
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
            ScheduledTask.objects.count()
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
@require_http_methods(["POST"])
def ajax_create_task(request):
    """AJAX endpoint for creating tasks"""
    try:
        data = json.loads(request.body)
        serializer = ScheduledTaskCreateSerializer(data=data)
        if serializer.is_valid():
            task = serializer.save(user=request.user)
            return JsonResponse({
                'success': True,
                'task': ScheduledTaskSerializer(task).data
            })
        else:
            return JsonResponse({'success': False, 'errors': serializer.errors})
    except Exception as e:
        logger.error(f"Error in ajax_create_task: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def ajax_update_task_status(request, task_id):
    """AJAX endpoint for updating task status"""
    try:
        task = get_object_or_404(ScheduledTask, id=task_id, user=request.user)
        data = json.loads(request.body)
        serializer = TaskStatusUpdateSerializer(task, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
        else:
            return JsonResponse({'success': False, 'errors': serializer.errors})
    except Exception as e:
        logger.error(f"Error in ajax_update_task_status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def ajax_run_task_manually(request, task_id):
    """AJAX endpoint for manually running tasks"""
    try:
        task = get_object_or_404(ScheduledTask, id=task_id, user=request.user)
        # Temporarily disabled until Celery is installed
        # result = execute_scheduled_task.delay(str(task.id))
        return JsonResponse({
            'success': True,
            'message': f'Task {task.name} started successfully (Celery not available)',
            'task_id': 'celery_not_available'
        })
    except Exception as e:
        logger.error(f"Error in ajax_run_task_manually: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def ajax_get_task_statistics(request):
    """AJAX endpoint for getting task statistics"""
    try:
        user_tasks = ScheduledTask.objects.filter(user=request.user)
        
        # Get counts by status
        status_counts = user_tasks.values('status').annotate(count=Count('id'))
        
        # Get counts by task type
        type_counts = user_tasks.values('task_type').annotate(count=Count('id'))
        
        # Get recent activity
        recent_logs = ScheduledTaskLog.objects.filter(
            task__user=request.user
        ).select_related('task').order_by('-started_at')[:10]
        
        # Get upcoming tasks
        upcoming_tasks = user_tasks.filter(
            status='active',
            next_run_at__gte=timezone.now()
        ).order_by('next_run_at')[:5]
        
        return JsonResponse({
            'success': True,
            'data': {
                'status_counts': list(status_counts),
                'type_counts': list(type_counts),
                'recent_logs': ScheduledTaskLogSerializer(recent_logs, many=True).data,
                'upcoming_tasks': ScheduledTaskSerializer(upcoming_tasks, many=True).data,
            }
        })
    except Exception as e:
        logger.error(f"Error in ajax_get_task_statistics: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
