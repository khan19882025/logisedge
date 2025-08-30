from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Facility, FacilityLocation


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Admin configuration for Facility model"""
    
    list_display = [
        'facility_code', 'facility_name', 'facility_type', 'status', 'city', 
        'contact_person', 'total_area', 'monthly_rent', 'currency',
        'is_owned', 'created_at', 'is_active_display'
    ]
    
    list_filter = [
        'facility_type', 'status', 'city', 'state', 'country', 'is_owned', 
        'has_security', 'has_cctv', 'has_climate_control', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'facility_code', 'facility_name', 'city', 'state', 'contact_person', 
        'address', 'description'
    ]
    
    list_editable = ['status']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'total_monthly_cost_display', 'utilization_rate_display', 'lease_status_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('facility_code', 'facility_name', 'facility_type', 'status')
        }),
        ('Description', {
            'fields': ('description', 'short_description'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'contact_person', 'contact_phone', 'contact_email'),
            'classes': ('collapse',)
        }),
        ('Specifications', {
            'fields': ('total_area', 'usable_area', 'height', 'capacity', 'max_weight_capacity'),
            'classes': ('collapse',)
        }),
        ('Operational', {
            'fields': ('operating_hours', 'timezone', 'is_24_7', 'has_security', 'has_cctv', 
                      'has_fire_suppression', 'has_climate_control')
        }),
        ('Equipment', {
            'fields': ('loading_docks', 'forklifts', 'pallet_racks', 'refrigeration_units', 'power_generators'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('monthly_rent', 'utilities_cost', 'maintenance_cost', 'currency', 
                      'total_monthly_cost_display')
        }),
        ('Ownership', {
            'fields': ('owner', 'lease_start_date', 'lease_end_date', 'is_owned', 'lease_status_display')
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['facility_name']
    
    list_per_page = 25
    
    date_hierarchy = 'created_at'
    
    actions = ['activate_facilities', 'deactivate_facilities', 'export_facilities']
    
    def is_active_display(self, obj):
        """Display active status with color coding"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inactive</span>'
            )
    is_active_display.short_description = 'Status'
    
    def total_monthly_cost_display(self, obj):
        """Display total monthly cost"""
        if obj.total_monthly_cost > 0:
            return format_html(
                '<span style="color: #007bff;">{:.2f} {}</span>',
                obj.total_monthly_cost, obj.currency
            )
        else:
            return f'0.00 {obj.currency}'
    total_monthly_cost_display.short_description = 'Total Monthly Cost'
    
    def utilization_rate_display(self, obj):
        """Display utilization rate"""
        if obj.utilization_rate > 0:
            return format_html(
                '<span style="color: #28a745;">{:.1f}%</span>',
                obj.utilization_rate
            )
        else:
            return '0.0%'
    utilization_rate_display.short_description = 'Utilization Rate'
    
    def lease_status_display(self, obj):
        """Display lease status with color coding"""
        status = obj.lease_status
        if status == 'Owned':
            return format_html(
                '<span style="color: #28a745;">✓ Owned</span>'
            )
        elif status == 'Active':
            return format_html(
                '<span style="color: #007bff;">Active</span>'
            )
        elif status == 'Expiring Soon':
            return format_html(
                '<span style="color: #ffc107;">⚠ Expiring Soon</span>'
            )
        elif status == 'Expired':
            return format_html(
                '<span style="color: #dc3545;">✗ Expired</span>'
            )
        else:
            return format_html(
                '<span style="color: #6c757d;">Unknown</span>'
            )
    lease_status_display.short_description = 'Lease Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def activate_facilities(self, request, queryset):
        """Action to activate selected facilities"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} facility(ies) were successfully activated.'
        )
    activate_facilities.short_description = "Activate selected facilities"
    
    def deactivate_facilities(self, request, queryset):
        """Action to deactivate selected facilities"""
        updated = queryset.update(status='inactive')
        self.message_user(
            request,
            f'{updated} facility(ies) were successfully deactivated.'
        )
    deactivate_facilities.short_description = "Deactivate selected facilities"
    
    def export_facilities(self, request, queryset):
        """Action to export selected facilities"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="facilities_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Facility Code', 'Facility Name', 'Type', 'Status', 'City', 'State',
            'Contact Person', 'Phone', 'Total Area', 'Monthly Rent', 'Currency',
            'Owner', 'Lease Status', 'Created Date'
        ])
        
        for facility in queryset:
            writer.writerow([
                facility.facility_code, facility.facility_name, facility.get_facility_type_display(), 
                facility.status, facility.city, facility.state, facility.contact_person,
                facility.phone, facility.total_area, facility.monthly_rent, facility.currency,
                facility.owner, facility.lease_status, facility.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    export_facilities.short_description = "Export selected facilities to CSV"


@admin.register(FacilityLocation)
class FacilityLocationAdmin(admin.ModelAdmin):
    """Admin configuration for FacilityLocation model"""
    
    list_display = [
        'full_location_code', 'location_name', 'facility', 'location_type', 'status',
        'current_utilization', 'reserved_capacity', 'is_available_display', 'created_at'
    ]
    
    list_filter = [
        'facility', 'location_type', 'status', 'has_climate_control', 'has_security',
        'is_accessible_by_forklift', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'location_code', 'location_name', 'facility__facility_name', 'facility__facility_code',
        'description'
    ]
    
    list_editable = ['status', 'current_utilization', 'reserved_capacity']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'available_capacity_display', 'location_path_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('facility', 'location_code', 'location_name', 'location_type', 'status')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Physical Specifications', {
            'fields': ('area', 'height', 'capacity', 'max_weight')
        }),
        ('Location Details', {
            'fields': ('floor_level', 'section', 'zone', 'location_path_display')
        }),
        ('Rack/Aisle Specific', {
            'fields': ('rack_number', 'aisle_number', 'bay_number', 'level_number'),
            'classes': ('collapse',)
        }),
        ('Coordinates', {
            'fields': ('x_coordinate', 'y_coordinate'),
            'classes': ('collapse',)
        }),
        ('Access & Restrictions', {
            'fields': ('access_restrictions', 'temperature_range', 'humidity_range')
        }),
        ('Equipment & Features', {
            'fields': ('has_lighting', 'has_climate_control', 'has_security', 'has_fire_suppression',
                      'is_accessible_by_forklift', 'is_accessible_by_pallet_jack')
        }),
        ('Utilization', {
            'fields': ('current_utilization', 'reserved_capacity', 'available_capacity_display')
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['facility', 'location_type', 'location_code']
    
    list_per_page = 25
    
    date_hierarchy = 'created_at'
    
    actions = ['activate_locations', 'deactivate_locations', 'reset_utilization']
    
    def is_available_display(self, obj):
        """Display availability status with color coding"""
        if obj.is_available:
            return format_html(
                '<span style="color: green;">✓ Available</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Unavailable</span>'
            )
    is_available_display.short_description = 'Availability'
    
    def available_capacity_display(self, obj):
        """Display available capacity"""
        if obj.available_capacity > 0:
            return format_html(
                '<span style="color: #28a745;">{:.2f} m³</span>',
                obj.available_capacity
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">0.00 m³</span>'
            )
    available_capacity_display.short_description = 'Available Capacity'
    
    def location_path_display(self, obj):
        """Display location path"""
        return obj.location_path
    location_path_display.short_description = 'Location Path'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('facility', 'created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def activate_locations(self, request, queryset):
        """Action to activate selected locations"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} location(s) were successfully activated.'
        )
    activate_locations.short_description = "Activate selected locations"
    
    def deactivate_locations(self, request, queryset):
        """Action to deactivate selected locations"""
        updated = queryset.update(status='inactive')
        self.message_user(
            request,
            f'{updated} location(s) were successfully deactivated.'
        )
    deactivate_locations.short_description = "Deactivate selected locations"
    
    def reset_utilization(self, request, queryset):
        """Action to reset utilization for selected locations"""
        updated = queryset.update(current_utilization=0, reserved_capacity=0)
        self.message_user(
            request,
            f'Utilization was reset for {updated} location(s).'
        )
    reset_utilization.short_description = "Reset utilization for selected locations"
