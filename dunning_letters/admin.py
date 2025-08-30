from django.contrib import admin
from .models import DunningLetter

@admin.register(DunningLetter)
class DunningLetterAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'invoice', 'level', 'status', 'overdue_amount', 
        'overdue_days', 'email_sent', 'created_at'
    ]
    list_filter = ['level', 'status', 'email_sent', 'created_at']
    search_fields = ['customer__customer_name', 'invoice__invoice_number', 'subject']
    readonly_fields = ['overdue_amount', 'overdue_days', 'due_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Customer & Invoice', {
            'fields': ('customer', 'invoice')
        }),
        ('Letter Details', {
            'fields': ('level', 'status', 'subject', 'content')
        }),
        ('Tracking Information', {
            'fields': ('overdue_amount', 'overdue_days', 'due_date'),
            'classes': ('collapse',)
        }),
        ('Email Information', {
            'fields': ('email_sent', 'email_sent_at', 'email_recipient'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'invoice')
