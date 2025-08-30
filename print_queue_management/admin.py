from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Printer, PrinterGroup, PrintTemplate, ERPEvent, 
    AutoPrintRule, PrintJob, BatchPrintJob, PrintJobLog
)


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'printer_type', 'location', 'status_display', 
        'active_jobs', 'is_active', 'created_at'
    ]
    list_filter = [
        'printer_type', 'is_active', 'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description', 'location', 'ip_address']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'printer_type', 'location')
        }),
        ('Network Configuration', {
            'fields': ('ip_address', 'port', 'driver_name'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'max_job_size')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        status = obj.get_status()
        color_map = {
            'idle': 'success',
            'busy': 'warning',
            'queue_full': 'danger',
            'offline': 'secondary'
        }
        color = color_map.get(status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, status.title()
        )
    status_display.short_description = 'Status'
    
    def active_jobs(self, obj):
        count = obj.print_jobs.filter(status__in=['queued', 'processing', 'printing']).count()
        return format_html(
            '<span class="badge badge-info">{}</span>',
            count
        )
    active_jobs.short_description = 'Active Jobs'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PrinterGroup)
class PrinterGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'printer_count', 'load_balancing', 'failover', 
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'load_balancing', 'failover', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    filter_horizontal = ['printers']
    
    def printer_count(self, obj):
        count = obj.printers.count()
        return format_html(
            '<span class="badge badge-info">{}</span>',
            count
        )
    printer_count.short_description = 'Printers'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PrintTemplate)
class PrintTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['template_type', 'is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'template_content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'description')
        }),
        ('Template Content', {
            'fields': ('template_file', 'template_content', 'variables')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ERPEvent)
class ERPEventAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'event_type', 'event_code', 'is_active', 'created_at'
    ]
    list_filter = ['event_type', 'is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'event_code']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AutoPrintRule)
class AutoPrintRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'erp_event', 'print_template', 'printer_display', 
        'priority', 'is_active', 'created_at'
    ]
    list_filter = [
        'priority', 'is_active', 'batch_printing', 'preview_required', 
        'auto_print', 'created_at'
    ]
    search_fields = ['name', 'description', 'erp_event__name', 'print_template__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'erp_event', 'print_template')
        }),
        ('Printer Assignment', {
            'fields': ('printer', 'printer_group'),
            'description': 'Specify either a printer or printer group, not both.'
        }),
        ('Printing Settings', {
            'fields': ('priority', 'conditions', 'preview_required', 'auto_print')
        }),
        ('Batch Printing', {
            'fields': ('batch_printing', 'batch_schedule'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('retry_count', 'retry_delay'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def printer_display(self, obj):
        if obj.printer:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:print_queue_management_printer_change', args=[obj.printer.id]),
                obj.printer.name
            )
        elif obj.printer_group:
            return format_html(
                '<a href="{}">Group: {}</a>',
                reverse('admin:print_queue_management_printergroup_change', args=[obj.printer_group.id]),
                obj.printer_group.name
            )
        return 'Not assigned'
    printer_display.short_description = 'Printer/Group'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = [
        'job_number', 'print_template', 'printer_display', 'status_display', 
        'priority', 'pages', 'copies', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'preview_required', 'created_at', 'started_at', 'completed_at'
    ]
    search_fields = ['job_number', 'print_template__name', 'printer__name']
    readonly_fields = [
        'id', 'job_number', 'created_at', 'updated_at', 'started_at', 
        'completed_at', 'created_by', 'updated_by'
    ]
    fieldsets = (
        ('Job Information', {
            'fields': ('job_number', 'print_template', 'printer', 'printer_group')
        }),
        ('Print Settings', {
            'fields': ('priority', 'pages', 'copies', 'preview_required', 'scheduled_at')
        }),
        ('Job Data', {
            'fields': ('data', 'file_path', 'preview_file'),
            'classes': ('collapse',)
        }),
        ('Status Information', {
            'fields': ('status', 'error_message', 'retry_count', 'max_retries')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def printer_display(self, obj):
        if obj.printer:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:print_queue_management_printer_change', args=[obj.printer.id]),
                obj.printer.name
            )
        elif obj.printer_group:
            return format_html(
                '<a href="{}">Group: {}</a>',
                reverse('admin:print_queue_management_printergroup_change', args=[obj.printer_group.id]),
                obj.printer_group.name
            )
        return 'Not assigned'
    printer_display.short_description = 'Printer/Group'
    
    def status_display(self, obj):
        color_map = {
            'queued': 'warning',
            'processing': 'info',
            'printing': 'success',
            'completed': 'primary',
            'failed': 'danger',
            'cancelled': 'secondary',
            'retrying': 'warning'
        }
        color = color_map.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.status.title()
        )
    status_display.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['cancel_jobs', 'retry_failed_jobs']
    
    def cancel_jobs(self, request, queryset):
        cancelled = 0
        for job in queryset.filter(status__in=['queued', 'processing']):
            job.status = 'cancelled'
            job.updated_by = request.user
            job.save()
            cancelled += 1
        
        self.message_user(
            request, 
            f'Successfully cancelled {cancelled} print jobs.'
        )
    cancel_jobs.short_description = 'Cancel selected jobs'
    
    def retry_failed_jobs(self, request, queryset):
        retried = 0
        for job in queryset.filter(status='failed'):
            if job.retry_count < job.max_retries:
                job.status = 'retrying'
                job.retry_count += 1
                job.updated_by = request.user
                job.save()
                retried += 1
        
        self.message_user(
            request, 
            f'Successfully initiated retry for {retried} failed jobs.'
        )
    retry_failed_jobs.short_description = 'Retry failed jobs'


@admin.register(BatchPrintJob)
class BatchPrintJobAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'auto_print_rule', 'scheduled_at', 'status_display', 
        'progress_display', 'created_at'
    ]
    list_filter = ['status', 'scheduled_at', 'created_at']
    search_fields = ['name', 'description', 'auto_print_rule__name']
    readonly_fields = [
        'id', 'total_jobs', 'completed_jobs', 'failed_jobs', 
        'started_at', 'completed_at', 'created_at', 'updated_at', 
        'created_by', 'updated_by'
    ]
    
    def status_display(self, obj):
        color_map = {
            'scheduled': 'info',
            'processing': 'warning',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'secondary'
        }
        color = color_map.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.status.title()
        )
    status_display.short_description = 'Status'
    
    def progress_display(self, obj):
        percentage = obj.get_progress_percentage()
        color = 'success' if percentage == 100 else 'warning'
        return format_html(
            '<div class="progress" style="width: 100px; height: 20px;">'
            '<div class="progress-bar bg-{}" style="width: {}%">{:.0f}%</div>'
            '</div>',
            color, percentage, percentage
        )
    progress_display.short_description = 'Progress'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PrintJobLog)
class PrintJobLogAdmin(admin.ModelAdmin):
    list_display = [
        'print_job', 'action', 'user', 'ip_address', 'created_at'
    ]
    list_filter = ['action', 'created_at', 'user']
    search_fields = ['print_job__job_number', 'message', 'user__username']
    readonly_fields = [
        'id', 'print_job', 'action', 'message', 'details', 
        'ip_address', 'user_agent', 'created_at', 'user'
    ]
    fieldsets = (
        ('Log Information', {
            'fields': ('print_job', 'action', 'message', 'details')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs


# Customize admin site
admin.site.site_header = 'Print Queue Management Admin'
admin.site.site_title = 'Print Queue Management'
admin.site.index_title = 'Print Queue Management Administration'

# Register models with custom admin classes
# (Already done above with decorators)
