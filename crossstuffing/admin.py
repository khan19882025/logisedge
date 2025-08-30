from django.contrib import admin
from .models import CrossStuffing, CrossStuffingCargo, CrossStuffingSummary


@admin.register(CrossStuffing)
class CrossStuffingAdmin(admin.ModelAdmin):
    list_display = [
        'cs_number', 'title', 'customer', 'facility', 'status', 
        'priority', 'scheduled_date', 'container_number', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'facility', 'container_size', 
        'container_type', 'currency', 'document_type', 'payment_mode',
        'ship_mode', 'destination', 'created_at', 'scheduled_date'
    ]
    search_fields = [
        'cs_number', 'title', 'customer__customer_name', 'facility__facility_name',
        'container_number', 'job__job_code', 'bl_number', 'boe', 'vessel'
    ]
    readonly_fields = ['cs_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('cs_number', 'title', 'description', 'document_type')
        }),
        ('Customer & Billing Information', {
            'fields': ('customer', 'bill_to', 'bill_to_customer', 'bill_to_address', 'deliver_to_customer', 'deliver_to_address')
        }),
        ('Related Records', {
            'fields': ('job', 'facility')
        }),
        ('Port Information', {
            'fields': ('port_of_loading', 'discharge_port', 'exit_point')
        }),
        ('Shipping Details', {
            'fields': ('cs_date', 'payment_mode', 'container_number', 'bl_number', 'boe')
        }),
        ('Vessel & Voyage', {
            'fields': ('destination', 'ship_mode', 'ship_date', 'vessel', 'voyage', 'delivery_terms')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'completed_date', 'status', 'priority')
        }),
        ('Container Details', {
            'fields': ('container_size', 'container_type')
        }),
        ('Cargo Details', {
            'fields': ('cargo_description', 'total_packages', 'total_weight', 'total_volume')
        }),
        ('Financial Information', {
            'fields': ('charges', 'currency')
        }),
        ('Additional Information', {
            'fields': ('notes', 'special_instructions')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new records
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrossStuffingCargo)
class CrossStuffingCargoAdmin(admin.ModelAdmin):
    list_display = [
        'crossstuffing', 'job_cargo', 'quantity', 'rate', 'amount', 
        'net_weight', 'gross_weight', 'ed_number', 'created_at'
    ]
    list_filter = [
        'crossstuffing__status', 'crossstuffing__customer', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'crossstuffing__cs_number', 'crossstuffing__title',
        'job_cargo__job__job_code', 'job_cargo__item_code',
        'ed_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Cross Stuffing Information', {
            'fields': ('crossstuffing', 'job_cargo')
        }),
        ('Cargo Details', {
            'fields': ('quantity', 'rate', 'amount', 'net_weight', 'gross_weight')
        }),
        ('Additional Information', {
            'fields': ('ed_number', 'remark')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 


@admin.register(CrossStuffingSummary)
class CrossStuffingSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'crossstuffing', 'job_no', 'items', 'qty', 'imp_cntr', 'size', 'seal',
        'exp_cntr', 'exp_size', 'exp_seal', 'created_at'
    ]
    list_filter = [
        'crossstuffing__status', 'crossstuffing__customer', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'crossstuffing__cs_number', 'crossstuffing__title',
        'job_no', 'items', 'imp_cntr', 'exp_cntr'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Cross Stuffing Information', {
            'fields': ('crossstuffing', 'job_no', 'items', 'qty')
        }),
        ('Import Container Details', {
            'fields': ('imp_cntr', 'size', 'seal')
        }),
        ('Export Container Details', {
            'fields': ('exp_cntr', 'exp_size', 'exp_seal')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 