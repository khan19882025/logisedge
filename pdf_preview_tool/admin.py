from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Document, DocumentType, PreviewSession, PreviewAction,
    DocumentAccessLog, PreviewSettings, SignatureStamp
)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'requires_approval', 'created_at']
    list_filter = ['category', 'is_active', 'requires_approval', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_approval')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'document_type', 'status', 'is_public', 'page_count',
        'file_size_mb', 'created_by', 'created_at'
    ]
    list_filter = [
        'document_type', 'status', 'is_public', 'created_at',
        'document_type__category'
    ]
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'document_type', 'description', 'status')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'page_count')
        }),
        ('Access Control', {
            'fields': ('is_public', 'allowed_roles', 'allowed_users')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['updated_at']
    filter_horizontal = ['allowed_users']
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = "File Size (MB)"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'document_type', 'created_by', 'updated_by'
        )


@admin.register(PreviewSession)
class PreviewSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'document_title', 'user', 'started_at',
        'duration_formatted', 'ip_address'
    ]
    list_filter = ['started_at', 'document__document_type']
    search_fields = ['id', 'document__title', 'user__username']
    ordering = ['-started_at']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'document', 'user')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'duration_seconds')
        }),
        ('Technical Details', {
            'fields': ('user_agent', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'started_at', 'duration_seconds']
    
    def document_title(self, obj):
        """Display document title with link"""
        if obj.document:
            url = reverse('admin:pdf_preview_tool_document_change', args=[obj.document.id])
            return format_html('<a href="{}">{}</a>', url, obj.document.title)
        return "N/A"
    document_title.short_description = "Document"
    
    def duration_formatted(self, obj):
        """Format duration in human-readable format"""
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return "N/A"
    duration_formatted.short_description = "Duration"


@admin.register(PreviewAction)
class PreviewActionAdmin(admin.ModelAdmin):
    list_display = [
        'action_type', 'user', 'document_title',
        'timestamp', 'session_link'
    ]
    list_filter = ['action_type', 'timestamp', 'session__document__document_type']
    search_fields = ['session__user__username', 'session__document__title']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Information', {
            'fields': ('session', 'action_type', 'timestamp')
        }),
        ('Details', {
            'fields': ('details',)
        }),
    )
    
    readonly_fields = ['timestamp']
    
    def user(self, obj):
        """Display user from session"""
        return obj.session.user if obj.session else "N/A"
    user.short_description = "User"
    
    def document_title(self, obj):
        """Display document title from session"""
        return obj.session.document.title if obj.session and obj.session.document else "N/A"
    document_title.short_description = "Document"
    
    def session_link(self, obj):
        """Display session ID with link"""
        if obj.session:
            url = reverse('admin:pdf_preview_tool_previewsession_change', args=[obj.session.id])
            return format_html('<a href="{}">{}</a>', url, str(obj.session.id)[:8])
        return "N/A"
    session_link.short_description = "Session"


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'document_title', 'access_type', 'timestamp',
        'ip_address', 'success'
    ]
    list_filter = ['access_type', 'timestamp', 'document__document_type', 'success']
    search_fields = ['user__username', 'document__title']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Access Information', {
            'fields': ('document', 'user', 'access_type', 'timestamp')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'success', 'error_message')
        }),
    )
    
    readonly_fields = ['timestamp']
    
    def document_title(self, obj):
        """Display document title with link"""
        if obj.document:
            url = reverse('admin:pdf_preview_tool_document_change', args=[obj.document.id])
            return format_html('<a href="{}">{}</a>', url, obj.document.title)
        return "N/A"
    document_title.short_description = "Document"


@admin.register(PreviewSettings)
class PreviewSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_zoom', 'show_thumbnails', 'theme', 'updated_at']
    list_filter = ['theme', 'updated_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['user__username']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Display Preferences', {
            'fields': ('default_zoom', 'show_thumbnails', 'auto_fit_page', 'theme')
        }),
        ('Features', {
            'fields': ('enable_annotations',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(SignatureStamp)
class SignatureStampAdmin(admin.ModelAdmin):
    """Admin interface for SignatureStamp model"""
    list_display = ['user', 'file', 'file_size_mb', 'file_extension', 'uploaded_at', 'updated_at']
    list_filter = ['uploaded_at', 'updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size_mb', 'file_extension']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('File Information', {
            'fields': ('file', 'file_size_mb', 'file_extension')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Only superusers can add signatures manually"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can modify signatures"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete signatures"""
        return request.user.is_superuser


# Custom admin site configuration
admin.site.site_header = "PDF Preview Tool Administration"
admin.site.site_title = "PDF Preview Tool Admin"
admin.site.index_title = "Welcome to PDF Preview Tool Administration"
