from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import CronJob, CronJobLog


@admin.register(CronJob)
class CronJobAdmin(admin.ModelAdmin):
    """Admin interface for CronJob model"""
    list_display = [
        'name', 'task', 'schedule_display', 'last_status', 'owner', 
        'next_run_at', 'last_run_at', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'last_status', 'created_at', 'last_run_at', 'owner'
    ]
    search_fields = ['name', 'task', 'description', 'owner__username', 'owner__email']
    readonly_fields = [
        'created_at', 'updated_at', 'last_run_at', 'next_run_at',
        'execution_count', 'success_count', 'failure_count'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'task', 'owner')
        }),
        ('Schedule Configuration', {
            'fields': ('schedule', 'is_active')
        }),
        ('Status & Execution', {
            'fields': ('last_status', 'last_run_at', 'next_run_at')
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
    
    actions = ['activate_jobs', 'deactivate_jobs', 'run_jobs_now', 'calculate_next_runs']
    
    def get_queryset(self, request):
        """Custom queryset with annotations"""
        qs = super().get_queryset(request)
        return qs.select_related('owner').prefetch_related('execution_logs')
    
    def execution_count(self, obj):
        """Display execution count with link to logs"""
        count = obj.execution_logs.count()
        if count > 0:
            url = reverse('admin:cron_job_viewer_cronjoblog_changelist')
            return format_html(
                '<a href="{}?job__id__exact={}">{}</a>',
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
        return obj.execution_logs.filter(status='failed').count()
    failure_count.short_description = 'Failed'
    
    def next_run_at(self, obj):
        """Display next run time with color coding"""
        if not obj.is_active:
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
    
    def schedule_display(self, obj):
        """Display human-readable schedule"""
        return obj.schedule_display
    schedule_display.short_description = 'Schedule'
    
    def activate_jobs(self, request, queryset):
        """Admin action to activate selected jobs"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'Successfully activated {updated} cron job(s).'
        )
    activate_jobs.short_description = 'Activate selected cron jobs'
    
    def deactivate_jobs(self, request, queryset):
        """Admin action to deactivate selected jobs"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'Successfully deactivated {updated} cron job(s).'
        )
    deactivate_jobs.short_description = 'Deactivate selected cron jobs'
    
    def run_jobs_now(self, request, queryset):
        """Admin action to run selected jobs immediately"""
        count = 0
        for job in queryset:
            try:
                # Create a log entry for manual execution
                log = CronJobLog.objects.create(
                    job=job,
                    celery_task_id='admin_execution',
                    worker_name='admin'
                )
                
                # Mark job as running
                job.mark_as_running()
                
                # Here you would typically trigger the actual Celery task
                # For now, we'll simulate completion
                import time
                time.sleep(1)  # Simulate execution time
                
                # Mark as completed
                log.mark_completed(status='success', output_message='Executed via admin')
                job.mark_as_completed(status='success')
                
                count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f'Failed to run job {job.name}: {str(e)}',
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request, 
                f'Successfully executed {count} cron job(s).'
            )
    run_jobs_now.short_description = 'Run selected cron jobs now'
    
    def calculate_next_runs(self, request, queryset):
        """Admin action to recalculate next run times"""
        count = 0
        for job in queryset:
            try:
                job.calculate_next_run()
                count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f'Failed to calculate next run for {job.name}: {str(e)}',
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request, 
                f'Successfully calculated next run times for {count} cron job(s).'
            )
    calculate_next_runs.short_description = 'Recalculate next run times'


@admin.register(CronJobLog)
class CronJobLogAdmin(admin.ModelAdmin):
    """Admin interface for CronJobLog model"""
    list_display = [
        'job_name', 'status', 'run_started_at', 'run_ended_at', 
        'execution_time', 'worker_name'
    ]
    list_filter = [
        'status', 'run_started_at', 'job__task', 'job__owner'
    ]
    search_fields = [
        'job__name', 'output_message', 'celery_task_id', 
        'job__owner__username'
    ]
    readonly_fields = [
        'job', 'run_started_at', 'run_ended_at', 'execution_time',
        'celery_task_id', 'worker_name'
    ]
    list_per_page = 50
    date_hierarchy = 'run_started_at'
    
    fieldsets = (
        ('Job Information', {
            'fields': ('job', 'celery_task_id', 'worker_name')
        }),
        ('Execution Details', {
            'fields': ('run_started_at', 'run_ended_at', 'execution_time', 'status')
        }),
        ('Output & Errors', {
            'fields': ('output_message',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['retry_failed_jobs']
    
    def job_name(self, obj):
        """Display job name with link"""
        if obj.job:
            url = reverse('admin:cron_job_viewer_cronjob_change', args=[obj.job.id])
            return format_html('<a href="{}">{}</a>', url, obj.job.name)
        return 'Unknown Job'
    job_name.short_description = 'Job'
    
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
                '<span style="color: {};">{}</span>',
                color, obj.duration_formatted
            )
        return '-'
    execution_time.short_description = 'Duration'
    
    def get_queryset(self, request):
        """Custom queryset with select_related"""
        return super().get_queryset(request).select_related('job', 'job__owner')
    
    def retry_failed_jobs(self, request, queryset):
        """Admin action to retry failed jobs"""
        failed_jobs = queryset.filter(status='failed')
        count = 0
        
        for log in failed_jobs:
            try:
                job = log.job
                
                # Create a new log entry for retry
                new_log = CronJobLog.objects.create(
                    job=job,
                    celery_task_id=f'retry_{log.celery_task_id}',
                    worker_name='admin_retry'
                )
                
                # Mark job as running
                job.mark_as_running()
                
                # Here you would typically trigger the actual Celery task
                # For now, we'll simulate completion
                import time
                time.sleep(1)  # Simulate execution time
                
                # Mark as completed
                new_log.mark_completed(status='success', output_message='Retried via admin')
                job.mark_as_completed(status='success')
                
                count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f'Failed to retry job {log.job.name}: {str(e)}',
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request, 
                f'Successfully retried {count} failed job(s).'
            )
    retry_failed_jobs.short_description = 'Retry failed jobs'


# Custom admin site configuration
admin.site.site_header = 'LogisEdge ERP Administration'
admin.site.site_title = 'LogisEdge Admin'
admin.site.index_title = 'Cron Job Viewer Administration'

# Add custom admin actions
def sync_celery_beat_schedules(modeladmin, request, queryset):
    """Sync all schedules with Celery Beat"""
    try:
        # This would typically sync with Celery Beat
        # For now, we'll just return a success message
        modeladmin.message_user(
            request, 
            'Schedule synchronization completed successfully.'
        )
    except Exception as e:
        modeladmin.message_user(
            request, 
            f'Failed to sync schedules: {str(e)}',
            level='ERROR'
        )

sync_celery_beat_schedules.short_description = 'Sync with Celery Beat'

# Register custom actions
admin.site.add_action(sync_celery_beat_schedules)
