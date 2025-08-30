from django.contrib import admin
from django.utils.html import format_html
from .models import Charge

@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'item', 'charge_type', 'rate', 'amount', 
        'effective_date', 'status', 'created_by', 'created_at'
    ]
    list_filter = [
        'charge_type', 'status', 'effective_date', 'customer', 'item'
    ]
    search_fields = [
        'customer__customer_name', 'item__item_name', 'item__item_code', 'remarks'
    ]
    readonly_fields = [
        'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'item', 'charge_type', 'rate', 'amount')
        }),
        ('Dates & Status', {
            'fields': ('effective_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_charges', 'deactivate_charges', 'delete_charges']
    
    def activate_charges(self, request, queryset):
        count = queryset.update(status='active', updated_by=request.user)
        self.message_user(request, f"Activated {count} charge(s).")
    activate_charges.short_description = "Activate selected charges"
    
    def deactivate_charges(self, request, queryset):
        count = queryset.update(status='inactive', updated_by=request.user)
        self.message_user(request, f"Deactivated {count} charge(s).")
    deactivate_charges.short_description = "Deactivate selected charges"
    
    def delete_charges(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Deleted {count} charge(s).")
    delete_charges.short_description = "Delete selected charges"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'item', 'created_by', 'updated_by')
