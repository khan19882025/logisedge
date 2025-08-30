from django.contrib import admin
from .models import LGP, LGPItem, PackageType


@admin.register(PackageType)
class PackageTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'code', 'description']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


class LGPItemInline(admin.TabularInline):
    model = LGPItem
    extra = 1
    fields = [
        'line_number', 'hs_code', 'good_description', 'marks_and_nos',
        'package_type_new', 'package_type', 'quantity', 'weight', 'volume', 'value',
        'customs_declaration', 'remarks'
    ]
    ordering = ['line_number']


@admin.register(LGP)
class LGPAdmin(admin.ModelAdmin):
    list_display = [
        'lgp_number', 'customer', 'document_date', 'document_validity_date',
        'warehouse', 'status', 'created_at', 'created_by'
    ]
    list_filter = ['status', 'warehouse', 'document_date', 'created_at']
    search_fields = ['lgp_number', 'customer__customer_name', 'dpw_ref_no', 'free_zone_company_name', 'local_company_name']
    readonly_fields = ['lgp_number', 'created_at', 'updated_at', 'created_by']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['lgp_number', 'status', 'created_by', 'created_at', 'updated_at']
        }),
        ('Document Details', {
            'fields': [
                ('customer', 'warehouse'),
                ('dpw_ref_no',),
                ('document_date', 'document_validity_date'),
            ]
        }),
        ('Company Information', {
            'fields': [
                'free_zone_company_name',
                'local_company_name',
                'goods_coming_from',
                'purpose_of_entry',
            ]
        }),
        ('Dispatch Information', {
            'fields': ['dispatch_date', 'dispatched_by'],
            'classes': ['collapse']
        }),
        ('Additional Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [LGPItemInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LGPItem)
class LGPItemAdmin(admin.ModelAdmin):
    list_display = [
        'lgp', 'line_number', 'hs_code', 'good_description',
        'get_package_type_display', 'quantity', 'weight', 'volume', 'value'
    ]
    list_filter = ['package_type_new', 'package_type', 'lgp__status']
    search_fields = ['lgp__lgp_number', 'hs_code', 'good_description']
    ordering = ['lgp', 'line_number']
    
    def get_package_type_display(self, obj):
        return obj.get_package_type_display
    get_package_type_display.short_description = 'Package Type'
