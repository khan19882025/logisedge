from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    FreightBooking, Carrier, BookingCoordinator, BookingDocument,
    BookingCharge, BookingHistory
)


class BookingDocumentInline(admin.TabularInline):
    model = BookingDocument
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at']
    fields = ['document_type', 'file', 'description', 'uploaded_by', 'uploaded_at']


class BookingChargeInline(admin.TabularInline):
    model = BookingCharge
    extra = 0
    fields = ['charge_type', 'description', 'amount', 'currency']


class BookingHistoryInline(admin.TabularInline):
    model = BookingHistory
    extra = 0
    readonly_fields = ['action', 'user', 'timestamp', 'notes']
    fields = ['action', 'user', 'timestamp', 'notes']
    can_delete = False


@admin.register(FreightBooking)
class FreightBookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference', 'customer_link', 'shipment_type', 'status_badge',
        'origin_destination', 'carrier', 'total_cost_display', 'created_at'
    ]
    list_filter = [
        'status', 'shipment_type', 'carrier', 'booking_coordinator',
        'created_at', 'pickup_date', 'delivery_date'
    ]
    search_fields = [
        'booking_reference', 'customer__name', 'carrier__name',
        'cargo_description', 'commodity'
    ]
    readonly_fields = [
        'booking_reference', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'confirmed_date', 'transit_start_date', 'delivered_date'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('booking_reference', 'quotation', 'customer', 'shipment_type', 'status')
        }),
        ('Origin & Destination', {
            'fields': (
                'origin_country', 'origin_port', 'origin_city',
                'destination_country', 'destination_port', 'destination_city'
            )
        }),
        ('Carrier & Coordinator', {
            'fields': ('carrier', 'booking_coordinator')
        }),
        ('Cargo Details', {
            'fields': (
                'cargo_description', 'commodity', 'weight', 'volume', 'packages',
                'container_type', 'container_count'
            )
        }),
        ('Dates', {
            'fields': ('pickup_date', 'delivery_date')
        }),
        ('Financial Information', {
            'fields': ('freight_cost', 'additional_costs', 'total_cost', 'currency')
        }),
        ('Additional Information', {
            'fields': ('special_instructions', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BookingDocumentInline, BookingChargeInline, BookingHistoryInline]
    
    def customer_link(self, obj):
        if obj.customer:
            url = reverse('admin:freight_quotation_customer_change', args=[obj.customer.id])
            return format_html('<a href="{}">{}</a>', url, obj.customer.name)
        return '-'
    customer_link.short_description = 'Customer'
    
    def status_badge(self, obj):
        status_colors = {
            'draft': 'secondary',
            'booked': 'primary',
            'confirmed': 'info',
            'in_transit': 'warning',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def origin_destination(self, obj):
        return f"{obj.origin_city} → {obj.destination_city}"
    origin_destination.short_description = 'Route'
    
    def total_cost_display(self, obj):
        return f"{obj.currency} {obj.total_cost:,.2f}"
    total_cost_display.short_description = 'Total Cost'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:  # Existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'email', 'phone', 'country', 'is_active']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'code', 'contact_person', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'country')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingCoordinator)
class BookingCoordinatorAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'department', 'phone_extension', 'is_active']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'employee_id')
        }),
        ('Department Information', {
            'fields': ('department', 'phone_extension')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingDocument)
class BookingDocumentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'document_type', 'filename', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['booking__booking_reference', 'filename', 'description']
    readonly_fields = ['uploaded_by', 'uploaded_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('booking', 'document_type', 'file', 'filename')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('System Information', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingCharge)
class BookingChargeAdmin(admin.ModelAdmin):
    list_display = ['booking', 'charge_type', 'description', 'amount', 'currency', 'created_at']
    list_filter = ['charge_type', 'currency', 'created_at']
    search_fields = ['booking__booking_reference', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Charge Information', {
            'fields': ('booking', 'charge_type', 'description')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ['booking', 'action', 'user', 'timestamp', 'notes_preview']
    list_filter = ['action', 'timestamp']
    search_fields = ['booking__booking_reference', 'user__username', 'notes']
    readonly_fields = ['booking', 'action', 'user', 'timestamp', 'notes']
    date_hierarchy = 'timestamp'
    
    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return '-'
    notes_preview.short_description = 'Notes'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
