from django.contrib import admin
from .models import HBL, HBLItem, HBLCharge, HBLHistory, HBLReport


class HBLItemInline(admin.TabularInline):
    model = HBLItem
    extra = 1
    fields = ['container_no', 'container_size', 'seal_no', 'number_of_packages', 
              'package_type', 'description', 'gross_weight', 'net_weight', 'measurement']


class HBLChargeInline(admin.TabularInline):
    model = HBLCharge
    extra = 1
    fields = ['charge_type', 'amount', 'currency', 'description']


class HBLHistoryInline(admin.TabularInline):
    model = HBLHistory
    extra = 0
    readonly_fields = ['action', 'description', 'user', 'timestamp', 'old_values', 'new_values']
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(HBL)
class HBLAdmin(admin.ModelAdmin):
    list_display = [
        'hbl_number', 'mbl_number', 'shipper', 'consignee', 'ocean_vessel',
        'port_of_loading', 'port_of_discharge', 'status', 'created_at'
    ]
    list_filter = [
        'status', 'terms', 'created_at', 'shipped_on_board', 'issue_date',
        'freight_prepaid', 'freight_collect'
    ]
    search_fields = [
        'hbl_number', 'mbl_number', 'shipper__name', 'consignee__name',
        'notify_party__name', 'ocean_vessel', 'port_of_loading', 'port_of_discharge'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [HBLItemInline, HBLChargeInline, HBLHistoryInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hbl_number', 'mbl_number', 'status', 'shipped_on_board', 'issue_date')
        }),
        ('Parties', {
            'fields': ('shipper', 'consignee', 'notify_party')
        }),
        ('Shipping Information', {
            'fields': ('pre_carriage_by', 'place_of_receipt', 'ocean_vessel', 
                      'port_of_loading', 'port_of_discharge', 'place_of_delivery', 'terms')
        }),
        ('Cargo Information', {
            'fields': ('description_of_goods', 'number_of_packages', 'package_type',
                      'gross_weight', 'measurement')
        }),
        ('Freight Information', {
            'fields': ('freight_prepaid', 'freight_collect', 'freight_amount', 'currency')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'special_instructions')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HBLItem)
class HBLItemAdmin(admin.ModelAdmin):
    list_display = [
        'hbl', 'container_no', 'container_size', 'seal_no', 'number_of_packages',
        'package_type', 'gross_weight', 'net_weight', 'measurement'
    ]
    list_filter = ['container_size', 'package_type', 'created_at']
    search_fields = ['hbl__hbl_number', 'container_no', 'seal_no', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(HBLCharge)
class HBLChargeAdmin(admin.ModelAdmin):
    list_display = ['hbl', 'charge_type', 'amount', 'currency', 'description']
    list_filter = ['charge_type', 'currency', 'created_at']
    search_fields = ['hbl__hbl_number', 'charge_type', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(HBLHistory)
class HBLHistoryAdmin(admin.ModelAdmin):
    list_display = ['hbl', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['hbl__hbl_number', 'action', 'description']
    readonly_fields = ['hbl', 'action', 'description', 'user', 'timestamp', 'old_values', 'new_values']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False


@admin.register(HBLReport)
class HBLReportAdmin(admin.ModelAdmin):
    list_display = ['report_name', 'report_type', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['report_name', 'report_type']
    readonly_fields = ['generated_at', 'generated_by']
    date_hierarchy = 'generated_at'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)
