from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'activity_type', 'model_name', 'description', 'user', 'created_at'
    ]
    list_filter = [
        'activity_type', 'model_name', 'created_at', 'user'
    ]
    search_fields = [
        'description', 'model_name', 'user__username', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'activity_type', 'description', 'model_name', 'object_id', 'user', 
        'content_type', 'ip_address', 'user_agent', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('activity_type', 'description', 'model_name', 'object_id')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Related Object', {
            'fields': ('content_type',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Activity logs should only be created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Activity logs should not be editable
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete activity logs
