from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Container, ContainerBooking, ContainerTracking, 
    ContainerInventory, ContainerMovement, ContainerNotification
)
from django.utils import timezone
from datetime import timedelta

@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = [
        'container_number', 'container_type', 'size', 'status', 
        'current_location', 'line_operator', 'is_available', 'maintenance_status'
    ]
    list_filter = [
        'container_type', 'status', 'line_operator', 'purchase_date',
        ('next_maintenance', admin.DateFieldListFilter)
    ]
    search_fields = ['container_number', 'current_location', 'line_operator']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('container_number', 'container_type', 'size')
        }),
        ('Specifications', {
            'fields': ('tare_weight', 'max_payload')
        }),
        ('Status & Location', {
            'fields': ('status', 'current_location', 'yard_location')
        }),
        ('Operator Information', {
            'fields': ('line_operator', 'purchase_date')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance', 'next_maintenance')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_available(self, obj):
        return obj.is_available()
    is_available.boolean = True
    is_available.short_description = 'Available'
    
    def maintenance_status(self, obj):
        if obj.is_overdue_maintenance():
            return format_html('<span style="color: red;">Overdue</span>')
        elif obj.next_maintenance and obj.next_maintenance <= timezone.now().date() + timedelta(days=30):
            return format_html('<span style="color: orange;">Due Soon</span>')
        return format_html('<span style="color: green;">OK</span>')
    maintenance_status.short_description = 'Maintenance'

class ContainerTrackingInline(admin.TabularInline):
    model = ContainerTracking
    extra = 0
    readonly_fields = ['tracking_number', 'created_at']
    fields = ['milestone', 'location', 'event_date', 'is_completed', 'is_delayed']

class ContainerMovementInline(admin.TabularInline):
    model = ContainerMovement
    extra = 0
    readonly_fields = ['created_at']
    fields = ['movement_type', 'from_location', 'to_location', 'movement_date']

@admin.register(ContainerBooking)
class ContainerBookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_number', 'container', 'customer', 'container_type', 
        'pickup_date', 'drop_off_date', 'status', 'total_amount', 'status_badge'
    ]
    list_filter = [
        'status', 'container_type', 'soc_coc', 'pickup_date', 'drop_off_date',
        'booking_date'
    ]
    search_fields = [
        'booking_number', 'container__container_number', 
        'customer__name', 'pickup_location', 'drop_off_port'
    ]
    readonly_fields = ['booking_number', 'total_days', 'total_amount', 'booking_date', 'confirmed_date']
    inlines = [ContainerTrackingInline]
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_number', 'container', 'customer', 'status')
        }),
        ('Container Details', {
            'fields': ('container_type', 'container_size', 'soc_coc')
        }),
        ('Dates & Locations', {
            'fields': ('pickup_date', 'pickup_location', 'drop_off_date', 'drop_off_port')
        }),
        ('Cargo Information', {
            'fields': ('cargo_description', 'weight', 'volume')
        }),
        ('Financial', {
            'fields': ('rate', 'total_days', 'total_amount')
        }),
        ('Related Records', {
            'fields': ('freight_quotation', 'freight_booking'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('special_instructions', 'booking_confirmation_file', 'soc_coc_details'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('booking_date', 'confirmed_date'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'active': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(ContainerTracking)
class ContainerTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_number', 'container', 'milestone', 'location', 
        'event_date', 'is_completed', 'is_delayed', 'vessel_info'
    ]
    list_filter = [
        'milestone', 'is_completed', 'is_delayed', 'event_date',
        'container__container_type'
    ]
    search_fields = [
        'tracking_number', 'container__container_number', 
        'location', 'vessel_name', 'voyage_number'
    ]
    readonly_fields = ['tracking_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Tracking Information', {
            'fields': ('tracking_number', 'container_booking', 'container', 'milestone')
        }),
        ('Location & Vessel', {
            'fields': ('location', 'vessel_name', 'voyage_number')
        }),
        ('Dates', {
            'fields': ('event_date', 'eta', 'actual_date')
        }),
        ('Status', {
            'fields': ('is_completed', 'is_delayed', 'delay_reason')
        }),
        ('Additional Information', {
            'fields': ('notes', 'documents'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_info(self, obj):
        if obj.vessel_name:
            return f"{obj.vessel_name} ({obj.voyage_number})" if obj.voyage_number else obj.vessel_name
        return "-"
    vessel_info.short_description = 'Vessel'

@admin.register(ContainerInventory)
class ContainerInventoryAdmin(admin.ModelAdmin):
    list_display = [
        'container', 'port', 'terminal', 'yard', 'status', 
        'arrival_date', 'is_overstayed', 'overstay_days'
    ]
    list_filter = [
        'status', 'port', 'terminal', 'is_overstayed', 'arrival_date',
        'container__container_type'
    ]
    search_fields = [
        'container__container_number', 'port', 'terminal', 'yard'
    ]
    readonly_fields = ['is_overstayed', 'overstay_days', 'created_at', 'updated_at']
    fieldsets = (
        ('Container Information', {
            'fields': ('container', 'container_booking')
        }),
        ('Location Details', {
            'fields': ('port', 'terminal', 'yard', 'bay', 'row', 'tier')
        }),
        ('Status & Dates', {
            'fields': ('status', 'arrival_date', 'expected_departure', 'actual_departure')
        }),
        ('Overstay Information', {
            'fields': ('is_overstayed', 'overstay_days', 'overstay_reason')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def overstay_days(self, obj):
        if obj.is_overstayed:
            return obj.overstay_days
        return "-"
    overstay_days.short_description = 'Overstay Days'

@admin.register(ContainerMovement)
class ContainerMovementAdmin(admin.ModelAdmin):
    list_display = [
        'container', 'movement_type', 'from_location', 'to_location', 
        'movement_date', 'vessel_info'
    ]
    list_filter = [
        'movement_type', 'movement_date', 'container__container_type'
    ]
    search_fields = [
        'container__container_number', 'from_location', 'to_location',
        'vessel_name', 'voyage_number'
    ]
    readonly_fields = ['created_at']
    fieldsets = (
        ('Movement Information', {
            'fields': ('container', 'movement_type', 'from_location', 'to_location')
        }),
        ('Date & Vessel', {
            'fields': ('movement_date', 'vessel_name', 'voyage_number')
        }),
        ('Related Records', {
            'fields': ('container_booking', 'container_tracking'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_info(self, obj):
        if obj.vessel_name:
            return f"{obj.vessel_name} ({obj.voyage_number})" if obj.voyage_number else obj.vessel_name
        return "-"
    vessel_info.short_description = 'Vessel'

@admin.register(ContainerNotification)
class ContainerNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'notification_type', 'priority', 'title', 'recipient_name', 
        'is_sent', 'is_read', 'created_at', 'priority_badge'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_sent', 'is_read', 'created_at'
    ]
    search_fields = [
        'title', 'message', 'recipient_name', 'recipient_email',
        'container__container_number'
    ]
    readonly_fields = ['created_at', 'sent_at', 'read_at']
    fieldsets = (
        ('Notification Information', {
            'fields': ('notification_type', 'priority', 'title', 'message')
        }),
        ('Recipient', {
            'fields': ('recipient_name', 'recipient_email')
        }),
        ('Related Objects', {
            'fields': ('container', 'container_booking', 'container_tracking'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def priority_badge(self, obj):
        colors = {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
        color = colors.get(obj.priority, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def save_model(self, request, obj, form, change):
        # Auto-send email if recipient email is provided and notification is being created
        if not change and obj.recipient_email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                send_mail(
                    obj.title,
                    obj.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [obj.recipient_email],
                    fail_silently=False,
                )
                obj.is_sent = True
                obj.sent_at = timezone.now()
            except Exception:
                pass  # Don't fail the save if email fails
        
        super().save_model(request, obj, form, change)

# Custom admin site configuration
admin.site.site_header = "Container Management Admin"
admin.site.site_title = "Container Management"
admin.site.index_title = "Container Management Administration"
