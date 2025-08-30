from django.contrib import admin
from .models import FiscalYear, FiscalPeriod, FiscalSettings


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current', 'status', 'created_at']
    list_filter = ['status', 'is_current', 'created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'start_date', 'end_date', 'description')
        }),
        ('Status', {
            'fields': ('is_current', 'status')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Ensure only one current fiscal year
        if obj.is_current:
            FiscalYear.objects.exclude(pk=obj.pk).update(is_current=False)
        super().save_model(request, obj, form, change)


@admin.register(FiscalPeriod)
class FiscalPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'fiscal_year', 'start_date', 'end_date', 'period_type', 'status', 'is_current']
    list_filter = ['fiscal_year', 'period_type', 'status', 'is_current', 'created_at']
    search_fields = ['name', 'description', 'fiscal_year__name']
    date_hierarchy = 'start_date'
    ordering = ['fiscal_year', 'start_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('fiscal_year', 'name', 'start_date', 'end_date', 'description')
        }),
        ('Configuration', {
            'fields': ('period_type', 'status', 'is_current')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Ensure only one current period per fiscal year
        if obj.is_current:
            FiscalPeriod.objects.filter(fiscal_year=obj.fiscal_year).exclude(pk=obj.pk).update(is_current=False)
        super().save_model(request, obj, form, change)


@admin.register(FiscalSettings)
class FiscalSettingsAdmin(admin.ModelAdmin):
    list_display = ['default_fiscal_year_start_month', 'default_period_type', 'auto_create_periods']
    
    fieldsets = (
        ('Default Configuration', {
            'fields': ('default_fiscal_year_start_month', 'default_period_type')
        }),
        ('Automation', {
            'fields': ('auto_create_periods', 'allow_overlapping_periods', 'require_period_approval')
        }),
        ('Naming Conventions', {
            'fields': ('fiscal_year_naming_convention', 'period_naming_convention')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not FiscalSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False
