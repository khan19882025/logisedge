from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    NotificationTemplate, TemplateCategory, TemplatePlaceholder,
    TemplateTest, TemplateAuditLog, TemplateVersion, TemplatePermission
)
import json
from django.utils import timezone


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color_display', 'icon', 'is_active', 'template_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Styling', {
            'fields': ('color', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
                obj.color, obj.color
            )
        return '-'
    color_display.short_description = 'Color'
    
    def template_count(self, obj):
        return obj.templates.count()
    template_count.short_description = 'Templates'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'category', 'language', 'priority', 
        'is_active', 'is_approved', 'version', 'created_by', 'updated_at'
    ]
    list_filter = [
        'template_type', 'category', 'language', 'priority', 'is_active', 
        'requires_approval', 'is_approved', 'created_at'
    ]
    search_fields = ['name', 'description', 'content', 'subject']
    readonly_fields = [
        'id', 'placeholders', 'version', 'created_by', 'created_at', 
        'updated_by', 'updated_at'
    ]
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type', 'category', 'priority')
        }),
        ('Content', {
            'fields': ('subject', 'content', 'html_content')
        }),
        ('Localization', {
            'fields': ('language', 'is_default_language', 'parent_template')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_approval', 'is_approved', 'approved_by', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('tags', 'placeholders', 'version')
        }),
        ('Audit Information', {
            'fields': ('id', 'created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'created_by', 'updated_by')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_approved and obj.requires_approval:
            return self.readonly_fields + ('content', 'html_content', 'subject')
        return self.readonly_fields


@admin.register(TemplatePlaceholder)
class TemplatePlaceholderAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'display_name', 'placeholder_type', 'data_type', 
        'is_active', 'is_required', 'example_value'
    ]
    list_filter = ['placeholder_type', 'data_type', 'is_active', 'is_required']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['placeholder_type', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'placeholder_type')
        }),
        ('Configuration', {
            'fields': ('data_type', 'format_string', 'example_value')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_required')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TemplateVersion)
class TemplateVersionAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'version_number', 'changed_by', 'changed_at', 'change_reason'
    ]
    list_filter = ['changed_at', 'template__template_type']
    search_fields = ['template__name', 'change_reason']
    readonly_fields = ['id', 'template', 'version_number', 'changed_by', 'changed_at']
    ordering = ['-changed_at']
    
    fieldsets = (
        ('Version Information', {
            'fields': ('template', 'version_number')
        }),
        ('Content Snapshot', {
            'fields': ('content', 'html_content', 'subject')
        }),
        ('Change Details', {
            'fields': ('change_reason', 'changed_by', 'changed_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Versions are created automatically


@admin.register(TemplateTest)
class TemplateTestAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'status', 'tested_by', 'tested_at', 'recipient_email', 'recipient_phone'
    ]
    list_filter = ['status', 'tested_at', 'template__template_type']
    search_fields = ['template__name', 'recipient_email', 'recipient_phone']
    readonly_fields = [
        'id', 'template', 'tested_by', 'tested_at', 'status', 'sent_at', 'delivered_at'
    ]
    ordering = ['-tested_at']
    
    fieldsets = (
        ('Test Information', {
            'fields': ('template', 'status', 'tested_by', 'tested_at')
        }),
        ('Test Configuration', {
            'fields': ('test_data', 'recipient_email', 'recipient_phone', 'notes')
        }),
        ('Results', {
            'fields': ('sent_at', 'delivered_at', 'error_message', 'error_code')
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Tests are created through the application


@admin.register(TemplateAuditLog)
class TemplateAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'action', 'user', 'timestamp', 'change_reason', 'ip_address'
    ]
    list_filter = ['action', 'timestamp', 'template__template_type']
    search_fields = ['template__name', 'user__username', 'change_reason']
    readonly_fields = [
        'id', 'template', 'action', 'user', 'timestamp', 'old_values', 
        'new_values', 'ip_address', 'user_agent'
    ]
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('template', 'action', 'user', 'timestamp')
        }),
        ('Change Details', {
            'fields': ('change_reason', 'old_values', 'new_values')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Audit logs are created automatically
    
    def old_values_display(self, obj):
        if obj.old_values:
            return format_html('<pre>{}</pre>', json.dumps(obj.old_values, indent=2))
        return '-'
    old_values_display.short_description = 'Old Values'
    
    def new_values_display(self, obj):
        if obj.new_values:
            return format_html('<pre>{}</pre>', json.dumps(obj.new_values, indent=2))
        return '-'
    new_values_display.short_description = 'New Values'


@admin.register(TemplatePermission)
class TemplatePermissionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'permission_type', 'category', 'is_active', 'granted_by', 'granted_at'
    ]
    list_filter = ['permission_type', 'is_active', 'granted_at']
    search_fields = ['user__username', 'user__email', 'category__name']
    readonly_fields = ['granted_at']
    ordering = ['user__username', 'permission_type']
    
    fieldsets = (
        ('Permission Information', {
            'fields': ('user', 'permission_type', 'category')
        }),
        ('Settings', {
            'fields': ('is_active', 'granted_by', 'granted_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)


# Custom Admin Actions
@admin.action(description="Approve selected templates")
def approve_templates(modeladmin, request, queryset):
    updated = queryset.update(
        is_approved=True,
        approved_by=request.user,
        approved_at=timezone.now()
    )
    modeladmin.message_user(request, f"{updated} templates were successfully approved.")

@admin.action(description="Activate selected templates")
def activate_templates(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} templates were successfully activated.")

@admin.action(description="Deactivate selected templates")
def deactivate_templates(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} templates were successfully deactivated.")


# Add actions to NotificationTemplateAdmin
NotificationTemplateAdmin.actions = [approve_templates, activate_templates, deactivate_templates]


# Admin Site Configuration
admin.site.site_header = "Notification Templates Administration"
admin.site.site_title = "Notification Templates Admin"
admin.site.index_title = "Welcome to Notification Templates Administration"
