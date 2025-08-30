from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    LetterType, LetterTemplate, GeneratedLetter, LetterPlaceholder,
    LetterApproval, DocumentCategory, HRDocument, LetterHistory
)


@admin.register(LetterType)
class LetterTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(LetterTemplate)
class LetterTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'letter_type', 'language', 'is_active', 'created_by', 'created_at']
    list_filter = ['letter_type', 'language', 'is_active', 'created_at']
    search_fields = ['title', 'subject', 'content']
    list_editable = ['is_active']
    ordering = ['letter_type__name', 'language']
    raw_id_fields = ['created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('letter_type', 'language', 'title', 'subject')
        }),
        ('Content', {
            'fields': ('content', 'arabic_content'),
            'classes': ('wide',)
        }),
        ('Settings', {
            'fields': ('is_active', 'created_by')
        }),
    )


@admin.register(LetterPlaceholder)
class LetterPlaceholderAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'field_type', 'is_required', 'default_value']
    list_filter = ['field_type', 'is_required']
    search_fields = ['name', 'description']
    list_editable = ['is_required', 'default_value']
    ordering = ['name']


@admin.register(GeneratedLetter)
class GeneratedLetterAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'letter_type', 'employee_link', 'status', 
        'issue_date', 'created_by', 'created_at'
    ]
    list_filter = [
        'letter_type', 'status', 'issue_date', 'created_at', 
        'is_confidential', 'finalized_at', 'signed_at'
    ]
    search_fields = [
        'reference_number', 'employee__full_name', 'letter_type__name', 
        'subject', 'content'
    ]
    list_editable = ['status']
    ordering = ['-created_at']
    raw_id_fields = ['employee', 'created_by', 'finalized_by', 'signed_by']
    readonly_fields = ['reference_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('reference_number', 'letter_type', 'template', 'employee')
        }),
        ('Letter Content', {
            'fields': ('subject', 'content', 'arabic_content'),
            'classes': ('wide',)
        }),
        ('Dates', {
            'fields': ('issue_date', 'effective_date')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'created_by', 'created_at', 'updated_at')
        }),
        ('Finalization', {
            'fields': ('finalized_by', 'finalized_at'),
            'classes': ('collapse',)
        }),
        ('Signing', {
            'fields': ('signed_by', 'signed_at'),
            'classes': ('collapse',)
        }),
        ('Files', {
            'fields': ('pdf_file', 'signed_pdf'),
            'classes': ('collapse',)
        }),
        ('Additional', {
            'fields': ('notes', 'is_confidential'),
            'classes': ('collapse',)
        }),
    )
    
    def employee_link(self, obj):
        if obj.employee:
            url = reverse('admin:employees_employee_change', args=[obj.employee.id])
            return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
        return '-'
    employee_link.short_description = 'Employee'
    employee_link.admin_order_field = 'employee__full_name'


@admin.register(LetterApproval)
class LetterApprovalAdmin(admin.ModelAdmin):
    list_display = ['letter', 'approver', 'status', 'created_at', 'approved_at']
    list_filter = ['status', 'created_at', 'approved_at']
    search_fields = ['letter__reference_number', 'approver__username', 'comments']
    raw_id_fields = ['letter', 'approver']
    ordering = ['-created_at']


@admin.register(LetterHistory)
class LetterHistoryAdmin(admin.ModelAdmin):
    list_display = ['letter', 'action', 'user', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['letter__reference_number', 'user__username', 'details']
    raw_id_fields = ['letter', 'user']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(HRDocument)
class HRDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'file_type', 'file_size_display', 
        'is_active', 'is_public', 'uploaded_by', 'uploaded_at'
    ]
    list_filter = [
        'category', 'is_active', 'is_public', 'uploaded_at', 
        'file_type'
    ]
    search_fields = ['title', 'description', 'uploaded_by__username']
    list_editable = ['is_active', 'is_public']
    ordering = ['-uploaded_at']
    raw_id_fields = ['uploaded_by']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'title', 'description')
        }),
        ('File', {
            'fields': ('file', 'file_type', 'file_size')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_public', 'version')
        }),
        ('Tracking', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return '-'
    file_size_display.short_description = 'File Size'
    file_size_display.admin_order_field = 'file_size'
