from django.contrib import admin
from .models import Currency, ExchangeRate, CurrencySettings


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'is_base_currency', 'is_active', 'decimal_places', 'created_at']
    list_filter = ['is_active', 'is_base_currency', 'created_at']
    search_fields = ['code', 'name', 'symbol']
    list_editable = ['is_active', 'is_base_currency']
    ordering = ['code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'symbol', 'decimal_places')
        }),
        ('Status', {
            'fields': ('is_active', 'is_base_currency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'rate', 'rate_type', 'effective_date', 'is_active', 'created_at']
    list_filter = ['rate_type', 'is_active', 'effective_date', 'from_currency', 'to_currency']
    search_fields = ['from_currency__code', 'to_currency__code', 'notes']
    list_editable = ['is_active']
    ordering = ['-effective_date', 'from_currency', 'to_currency']
    
    fieldsets = (
        ('Currency Pair', {
            'fields': ('from_currency', 'to_currency')
        }),
        ('Rate Information', {
            'fields': ('rate', 'rate_type', 'effective_date', 'expiry_date')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CurrencySettings)
class CurrencySettingsAdmin(admin.ModelAdmin):
    list_display = ['default_currency', 'auto_update_rates', 'update_frequency', 'last_update']
    list_filter = ['auto_update_rates', 'update_frequency']
    
    fieldsets = (
        ('Default Settings', {
            'fields': ('default_currency',)
        }),
        ('API Configuration', {
            'fields': ('auto_update_rates', 'api_provider', 'api_key', 'update_frequency')
        }),
        ('Timestamps', {
            'fields': ('last_update', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_update', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not CurrencySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False 