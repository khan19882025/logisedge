from django.contrib import admin
from .models import PaymentSource


@admin.register(PaymentSource)
class PaymentSourceAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentSource model"""
    
    list_display = [
        'name', 'code', 'source_type', 'category', 'payment_type', 'linked_ledger_display', 
        'currency_display', 'active', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    
    list_filter = [
        'source_type', 'category', 'payment_type', 'active', 'currency', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'name', 'code', 'description', 'linked_ledger__name', 'linked_ledger__account_code',
        'default_expense_ledger__name', 'default_vendor__customer_name'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'active', 'remarks')
        }),
        ('Classification', {
            'fields': ('payment_type', 'source_type', 'category')
        }),
        ('Financial Settings', {
            'fields': ('currency', 'linked_ledger', 'default_expense_ledger')
        }),
        ('Vendor Settings', {
            'fields': ('default_vendor',),
            'classes': ('collapse',)
        }),
        ('Legacy Fields (Backward Compatibility)', {
            'fields': ('linked_account', 'is_active'),
            'classes': ('collapse',),
            'description': 'These fields are maintained for backward compatibility with existing records.'
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def linked_ledger_display(self, obj):
        """Display linked ledger in a readable format"""
        if obj.linked_ledger:
            return f"{obj.linked_ledger.account_code} - {obj.linked_ledger.name}"
        elif obj.linked_account:  # Legacy field
            return f"{obj.linked_account.account_code} - {obj.linked_account.name} (Legacy)"
        return "Not linked"
    linked_ledger_display.short_description = "Linked Ledger"
    
    def currency_display(self, obj):
        """Display currency in a readable format"""
        if obj.currency:
            return f"{obj.currency.code} - {obj.currency.name}"
        return "Not set"
    currency_display.short_description = "Currency"
    
    def save_model(self, request, obj, form, change):
        """Set the user when saving"""
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Show all payment sources including inactive ones"""
        return super().get_queryset(request)
    
    actions = ['activate_payment_sources', 'deactivate_payment_sources']
    
    def activate_payment_sources(self, request, queryset):
        """Activate selected payment sources"""
        updated = queryset.update(active=True, is_active=True)  # Keep both fields in sync
        self.message_user(
            request, 
            f"Successfully activated {updated} payment source(s)."
        )
    activate_payment_sources.short_description = "Activate selected payment sources"
    
    def deactivate_payment_sources(self, request, queryset):
        """Deactivate selected payment sources"""
        updated = queryset.update(active=False, is_active=False)  # Keep both fields in sync
        self.message_user(
            request, 
            f"Successfully deactivated {updated} payment source(s)."
        )
    deactivate_payment_sources.short_description = "Deactivate selected payment sources"
