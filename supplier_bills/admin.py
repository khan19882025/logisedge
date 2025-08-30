from django.contrib import admin
from .models import SupplierBill

@admin.register(SupplierBill)
class SupplierBillAdmin(admin.ModelAdmin):
    list_display = ['number', 'supplier', 'bill_date', 'due_date', 'amount', 'status', 'is_overdue', 'days_overdue']
    list_filter = ['status', 'bill_date', 'due_date']
    search_fields = ['number', 'supplier', 'reference_number']
    readonly_fields = ['number', 'created_at', 'updated_at']
    date_hierarchy = 'bill_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('number', 'supplier', 'bill_date', 'due_date', 'amount')
        }),
        ('Status & Reference', {
            'fields': ('status', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('description', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'
    
    def days_overdue(self, obj):
        return obj.days_overdue
    days_overdue.short_description = 'Days Overdue' 