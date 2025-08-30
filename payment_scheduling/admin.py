from django.contrib import admin
from .models import (
    PaymentSchedule, PaymentInstallment, PaymentReminder, 
    PaymentMethod, VATConfiguration, PaymentScheduleHistory
)


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'schedule_number', 'customer', 'vendor', 'total_amount', 
        'currency', 'status', 'due_date', 'created_at'
    ]
    list_filter = ['status', 'currency', 'payment_type', 'created_at']
    search_fields = ['schedule_number', 'customer__customer_name', 'vendor']
    readonly_fields = ['schedule_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('schedule_number', 'customer', 'vendor', 'payment_type')
        }),
        ('Amount Details', {
            'fields': ('total_amount', 'currency', 'vat_rate', 'vat_amount', 'total_with_vat')
        }),
        ('Schedule Information', {
            'fields': ('due_date', 'installment_count', 'installment_amount', 'status')
        }),
        ('References', {
            'fields': ('invoice_reference', 'po_reference', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = [
        'installment_number', 'payment_schedule', 'amount', 
        'due_date', 'status', 'paid_amount'
    ]
    list_filter = ['status', 'due_date', 'created_at']
    search_fields = ['payment_schedule__schedule_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = [
        'reminder_type', 'payment_schedule', 'scheduled_date', 
        'sent_date', 'status', 'recipient'
    ]
    list_filter = ['reminder_type', 'status', 'scheduled_date']
    search_fields = ['payment_schedule__schedule_number', 'recipient']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']


@admin.register(VATConfiguration)
class VATConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'vat_rate', 'is_active', 'created_at']
    list_filter = ['is_active', 'vat_rate']
    search_fields = ['name', 'description']


@admin.register(PaymentScheduleHistory)
class PaymentScheduleHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'payment_schedule', 'action', 'user', 'timestamp', 'description'
    ]
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['payment_schedule__schedule_number', 'description']
    readonly_fields = ['timestamp', 'user']
