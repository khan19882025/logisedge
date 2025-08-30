from django.contrib import admin
from .models import Salesman

@admin.register(Salesman)
class SalesmanAdmin(admin.ModelAdmin):
    list_display = ['salesman_code', 'get_full_name', 'email', 'phone', 'status', 'department', 'hire_date']
    list_filter = ['status', 'department', 'gender', 'hire_date']
    search_fields = ['salesman_code', 'first_name', 'last_name', 'email', 'phone']
    ordering = ['first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('salesman_code', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Employment Information', {
            'fields': ('hire_date', 'status', 'department', 'position', 'manager')
        }),
        ('Performance', {
            'fields': ('commission_rate', 'target_amount')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
