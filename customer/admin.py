from django.contrib import admin
from .models import Customer, CustomerType

@admin.register(CustomerType)
class CustomerTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_code', 'customer_name', 'contact_person', 'email', 'get_customer_types', 'is_active']
    list_filter = ['customer_types', 'is_active', 'portal_active', 'created_at']
    search_fields = ['customer_code', 'customer_name', 'contact_person', 'email']
    readonly_fields = ['customer_code', 'created_by', 'created_at', 'updated_by', 'updated_at']
    filter_horizontal = ['customer_types']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer_code', 'customer_name', 'contact_person', 'email', 'phone', 'mobile', 'fax', 'website', 'customer_types', 'industry', 'tax_number', 'registration_number')
        }),
        ('Addresses', {
            'fields': ('billing_address', 'billing_city', 'billing_state', 'billing_country', 'billing_postal_code', 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_country', 'shipping_postal_code')
        }),
        ('Financial', {
            'fields': ('credit_limit', 'payment_terms', 'currency', 'tax_exempt', 'tax_rate', 'discount_percentage')
        }),
        ('Customer Portal', {
            'fields': ('portal_username', 'portal_password', 'portal_active', 'portal_last_login')
        }),
        ('System Information', {
            'fields': ('is_active', 'notes', 'created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_types(self, obj):
        return obj.get_customer_types_display()
    get_customer_types.short_description = 'Customer Types'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new customer
            obj.created_by = request.user
        else:  # Updating existing customer
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
