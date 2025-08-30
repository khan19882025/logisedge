from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import ScheduledTask, ScheduledTaskLog, TaskSchedule


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    """Admin interface for ScheduledTask model"""
    list_display = [
        'name', 'task_type', 'schedule_type', 'status', 'user', 
        'next_run_at', 'last_run_at', 'created_at'
    ]
    list_filter = [
        'status', 'task_type', 'schedule_type', 'created_at', 
        'last_run_at', 'user'
    ]
    search_fields = ['name', 'description', 'user__username', 'user__email']
    readonly_fields = [
        'created_at', 'updated_at', 'last_run_at', 'next_run_at',
        'execution_count', 'success_count', 'failure_count'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'task_type', 'user')
        }),
        ('Schedule Configuration', {
            'fields': ('schedule_type', 'schedule_time', 'schedule_date', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'day_of_month')
        }),
        ('Status & Execution', {
            'fields': ('status', 'last_run_at', 'next_run_at')
        }),
        ('Statistics', {
            'fields': ('execution_count', 'success_count', 'failure_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_tasks', 'deactivate_tasks', 'run_tasks_now']
    
    def get_queryset(self, request):
        """Custom queryset with annotations"""
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('execution_logs')
    
    def execution_count(self, obj):
        """Display execution count with link to logs"""
        count = obj.execution_logs.count()
        if count > 0:
            url = reverse('admin:auto_task_scheduler_scheduledtasklog_changelist')
            return format_html(
                '<a href="{}?task__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    execution_count.short_description = 'Executions'
    
    def success_count(self, obj):
        """Display success count"""
        return obj.execution_logs.filter(status='success').count()
    success_count.short_description = 'Success'
    
    def failure_count(self, obj):
        """Display failure count"""
        return obj.execution_logs.filter(status='failure').count()
    failure_count.short_description = 'Failed'
    
    def next_run_at(self, obj):
        """Display next run time with color coding"""
        if obj.status == 'inactive':
            return format_html('<span style="color: #999;">Inactive</span>')
        
        if obj.next_run_at:
            now = timezone.now()
            if obj.next_run_at <= now:
                return format_html('<span style="color: #f00;">Overdue</span>')
            elif obj.next_run_at <= now + timedelta(minutes=30):
                return format_html('<span style="color: #f90;">Soon</span>')
            else:
                return obj.next_run_at.strftime('%Y-%m-%d %H:%M')
        return 'Not scheduled'
    next_run_at.short_description = 'Next Run'
    
    def activate_tasks(self, request, queryset):
        """Admin action to activate selected tasks"""
        updated = queryset.update(status='active')
        self.message_user(
            request, 
            f'Successfully activated {updated} task(s).'
        )
    activate_tasks.short_description = 'Activate selected tasks'
    
    def deactivate_tasks(self, request, queryset):
        """Admin action to deactivate selected tasks"""
        updated = queryset.update(status='inactive')
        self.message_user(
            request, 
            f'Successfully deactivated {updated} task(s).'
        )
    deactivate_tasks.short_description = 'Deactivate selected tasks'
    
    def run_tasks_now(self, request, queryset):
        """Admin action to run selected tasks immediately"""
        from .tasks import execute_scheduled_task
        
        count = 0
        for task in queryset:
            try:
                execute_scheduled_task.delay(str(task.id))
                count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f'Failed to run task {task.name}: {str(e)}',
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request, 
                f'Successfully queued {count} task(s) for immediate execution.'
            )
    run_tasks_now.short_description = 'Run selected tasks now'


@admin.register(ScheduledTaskLog)
class ScheduledTaskLogAdmin(admin.ModelAdmin):
    """Admin interface for ScheduledTaskLog model"""
    list_display = [
        'task_name', 'status', 'started_at', 'completed_at', 
        'execution_time', 'user'
    ]
    list_filter = [
        'status', 'started_at', 'task__task_type', 'task__user'
    ]
    search_fields = [
        'task__name', 'output_message', 'error_traceback', 
        'task__user__username'
    ]
    readonly_fields = [
        'task', 'started_at', 'completed_at', 'execution_time',
        'celery_task_id'
    ]
    list_per_page = 50
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Task Information', {
            'fields': ('task', 'celery_task_id')
        }),
        ('Execution Details', {
            'fields': ('started_at', 'completed_at', 'execution_time', 'status')
        }),
        ('Output & Errors', {
            'fields': ('output_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
    )
    
    def task_name(self, obj):
        """Display task name with link"""
        if obj.task:
            url = reverse('admin:auto_task_scheduler_scheduledtask_change', args=[obj.task.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.name)
        return 'Unknown Task'
    task_name.short_description = 'Task'
    
    def user(self, obj):
        """Display user with link"""
        if obj.task and obj.task.user:
            url = reverse('admin:auth_user_change', args=[obj.task.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.user.username)
        return 'Unknown User'
    user.short_description = 'User'
    
    def execution_time(self, obj):
        """Display execution time with color coding"""
        if obj.execution_time:
            if obj.execution_time < 60:
                color = '#0a0'
            elif obj.execution_time < 300:
                color = '#f90'
            else:
                color = '#f00'
            
            return format_html(
                '<span style="color: {};">{:.2f}s</span>',
                color, obj.execution_time
            )
        return '-'
    execution_time.short_description = 'Duration'
    
    def get_queryset(self, request):
        """Custom queryset with select_related"""
        return super().get_queryset(request).select_related('task', 'task__user')


@admin.register(TaskSchedule)
class TaskScheduleAdmin(admin.ModelAdmin):
    """Admin interface for TaskSchedule model"""
    list_display = [
        'task_name', 'schedule_key', 'is_registered', 
        'last_sync', 'created_at'
    ]
    list_filter = ['is_registered', 'created_at', 'last_sync']
    search_fields = ['task__name', 'schedule_key']
    readonly_fields = ['created_at', 'last_sync']
    list_per_page = 25
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('task', 'schedule_key')
        }),
        ('Celery Integration', {
            'fields': ('is_registered', 'last_sync')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def task_name(self, obj):
        """Display task name with link"""
        if obj.task:
            url = reverse('admin:auto_task_scheduler_scheduledtask_change', args=[obj.task.id])
            return format_html('<a href="{}">{}</a>', url, obj.task.name)
        return 'Unknown Task'
    task_name.short_description = 'Task'
    
    def get_queryset(self, request):
        """Custom queryset with select_related"""
        return super().get_queryset(request).select_related('task')


# Custom admin site configuration
admin.site.site_header = 'LogisEdge ERP Administration'
admin.site.site_title = 'LogisEdge Admin'
admin.site.index_title = 'Task Scheduler Administration'

# Add custom admin actions
def sync_all_schedules(modeladmin, request, queryset):
    """Sync all schedules with Celery beat"""
    from .tasks import sync_celery_schedules
    
    try:
        result = sync_celery_schedules.delay()
        modeladmin.message_user(
            request, 
            f'Schedule synchronization started. Task ID: {result.id}'
        )
    except Exception as e:
        modeladmin.message_user(
            request, 
            f'Failed to sync schedules: {str(e)}',
            level='ERROR'
        )

sync_all_schedules.short_description = 'Sync all schedules with Celery beat'

# Register custom actions
admin.site.add_action(sync_all_schedules)
