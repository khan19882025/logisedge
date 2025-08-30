from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Shipment, StatusUpdate, ShipmentAttachment, NotificationLog, 
    BulkUpdateLog, ShipmentSearch
)

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'shipment_id', 'container_number', 'customer_name', 'origin_port', 
        'destination_port', 'current_status', 'last_updated', 'is_tracking_enabled'
    ]
    list_filter = [
        'current_status', 'is_tracking_enabled', 'is_active', 'booking_date',
        'origin_country', 'destination_country', 'created_at'
    ]
    search_fields = [
        'shipment_id', 'container_number', 'booking_id', 'hbl_number', 
        'customer_reference', 'customer_name'
    ]
    readonly_fields = ['shipment_id', 'created_at', 'updated_at', 'last_updated']
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shipment_id', 'container_number', 'booking_id', 'hbl_number', 'customer_reference')
        }),
        ('Customer Information', {
            'fields': ('customer', 'customer_name', 'customer_email', 'customer_phone')
        }),
        ('Route Information', {
            'fields': ('origin_port', 'destination_port', 'origin_country', 'destination_country')
        }),
        ('Dates', {
            'fields': ('booking_date', 'expected_departure', 'expected_arrival', 'actual_departure', 'actual_arrival')
        }),
        ('Current Status', {
            'fields': ('current_status', 'current_location', 'last_updated')
        }),
        ('Vessel Information', {
            'fields': ('vessel_name', 'voyage_number', 'shipping_line')
        }),
        ('Cargo Information', {
            'fields': ('cargo_description', 'cargo_weight', 'cargo_volume')
        }),
        ('Tracking', {
            'fields': ('is_tracking_enabled', 'gps_coordinates')
        }),
        ('Notes', {
            'fields': ('internal_notes', 'customer_notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'created_by')
    
    def view_shipment_link(self, obj):
        if obj.pk:
            url = reverse('shipment_tracking:shipment_detail', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">View Details</a>', url)
        return '-'
    view_shipment_link.short_description = 'View Details'
    
    actions = ['mark_as_delivered', 'mark_as_in_transit', 'enable_tracking', 'disable_tracking']
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(current_status='delivered')
        self.message_user(request, f'{updated} shipments marked as delivered.')
    mark_as_delivered.short_description = 'Mark selected shipments as delivered'
    
    def mark_as_in_transit(self, request, queryset):
        updated = queryset.update(current_status='sailing')
        self.message_user(request, f'{updated} shipments marked as in transit.')
    mark_as_in_transit.short_description = 'Mark selected shipments as in transit'
    
    def enable_tracking(self, request, queryset):
        updated = queryset.update(is_tracking_enabled=True)
        self.message_user(request, f'Tracking enabled for {updated} shipments.')
    enable_tracking.short_description = 'Enable tracking for selected shipments'
    
    def disable_tracking(self, request, queryset):
        updated = queryset.update(is_tracking_enabled=False)
        self.message_user(request, f'Tracking disabled for {updated} shipments.')
    disable_tracking.short_description = 'Disable tracking for selected shipments'

@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = [
        'shipment', 'status', 'location', 'timestamp', 'updated_by'
    ]
    list_filter = ['status', 'timestamp', 'updated_by']
    search_fields = ['shipment__shipment_id', 'shipment__container_number', 'location']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 25
    
    fieldsets = (
        ('Shipment Information', {
            'fields': ('shipment',)
        }),
        ('Status Information', {
            'fields': ('status', 'location', 'description', 'estimated_completion')
        }),
        ('Location Data', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'updated_by', 'notification_sent', 'notification_sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shipment', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ShipmentAttachment)
class ShipmentAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'shipment', 'file_type', 'description', 'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['file_type', 'uploaded_at', 'uploaded_by']
    search_fields = ['shipment__shipment_id', 'description']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'uploaded_at'
    list_per_page = 25
    
    fieldsets = (
        ('Shipment Information', {
            'fields': ('shipment', 'status_update')
        }),
        ('File Information', {
            'fields': ('file', 'file_type', 'description')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shipment', 'status_update', 'uploaded_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'shipment', 'notification_type', 'recipient', 'sent_at', 'is_sent', 'is_delivered'
    ]
    list_filter = ['notification_type', 'is_sent', 'is_delivered', 'sent_at', 'sent_by']
    search_fields = ['shipment__shipment_id', 'recipient', 'subject']
    readonly_fields = ['sent_at']
    date_hierarchy = 'sent_at'
    list_per_page = 25
    
    fieldsets = (
        ('Shipment Information', {
            'fields': ('shipment', 'status_update')
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'recipient', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('is_sent', 'is_delivered', 'error_message')
        }),
        ('Metadata', {
            'fields': ('sent_at', 'sent_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shipment', 'status_update', 'sent_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.sent_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(BulkUpdateLog)
class BulkUpdateLogAdmin(admin.ModelAdmin):
    list_display = [
        'update_type', 'total_records', 'successful_updates', 'failed_updates', 
        'processed_by', 'processed_at'
    ]
    list_filter = ['update_type', 'processed_at', 'processed_by']
    readonly_fields = ['processed_at']
    date_hierarchy = 'processed_at'
    list_per_page = 25
    
    fieldsets = (
        ('Update Information', {
            'fields': ('update_type', 'file_uploaded')
        }),
        ('Results', {
            'fields': ('total_records', 'successful_updates', 'failed_updates')
        }),
        ('Details', {
            'fields': ('success_details', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('processed_by', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('processed_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ShipmentSearch)
class ShipmentSearchAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'search_query', 'search_type', 'search_results_count', 'searched_at'
    ]
    list_filter = ['search_type', 'searched_at', 'user']
    search_fields = ['search_query', 'user__username']
    readonly_fields = ['searched_at']
    date_hierarchy = 'searched_at'
    list_per_page = 25
    
    fieldsets = (
        ('Search Information', {
            'fields': ('user', 'search_query', 'search_type')
        }),
        ('Results', {
            'fields': ('search_results_count',)
        }),
        ('Metadata', {
            'fields': ('searched_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False  # Search logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Search logs should not be edited
