from django.contrib import admin
from .models import RFUser, ScanSession, ScanRecord, Location, Item


@admin.register(RFUser)
class RFUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'department', 'is_active', 'created_at']
    list_filter = ['department', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    ordering = ['-created_at']


@admin.register(ScanSession)
class ScanSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_type', 'start_time', 'end_time', 'is_active']
    list_filter = ['session_type', 'is_active', 'start_time']
    search_fields = ['user__employee_id', 'user__user__username']
    ordering = ['-start_time']
    readonly_fields = ['start_time']


@admin.register(ScanRecord)
class ScanRecordAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'session', 'item_name', 'quantity', 'location', 'scan_time']
    list_filter = ['session__session_type', 'scan_time', 'status']
    search_fields = ['barcode', 'item_name', 'item_code']
    ordering = ['-scan_time']
    readonly_fields = ['scan_time']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['location_code', 'location_name', 'location_type', 'is_active']
    list_filter = ['location_type', 'is_active', 'created_at']
    search_fields = ['location_code', 'location_name']
    ordering = ['location_code']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_code', 'item_name', 'barcode', 'unit', 'is_active']
    list_filter = ['unit', 'is_active', 'created_at']
    search_fields = ['item_code', 'item_name', 'barcode']
    ordering = ['item_code']
