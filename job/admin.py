from django.contrib import admin
from .models import Job, JobStatus, JobPriority

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_code', 'title', 'job_type', 'status', 'priority', 'assigned_to', 'created_at')
    list_filter = ('job_type', 'status', 'priority', 'created_at')
    search_fields = ('job_code', 'title', 'description')
    readonly_fields = ('job_code', 'created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(JobStatus)
class JobStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(JobPriority)
class JobPriorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'color', 'is_active')
    list_filter = ('is_active',)
    ordering = ('level',) 