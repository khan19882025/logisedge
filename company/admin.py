from django.contrib import admin
from company.company_model import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'email', 'phone']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Legal Information', {
            'fields': ('tax_number', 'registration_number'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at'] 