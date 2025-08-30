from django.contrib import admin
from .models import PettyCashDay, PettyCashEntry, PettyCashBalance, PettyCashAudit

class PettyCashEntryInline(admin.TabularInline):
    model = PettyCashEntry
    extra = 1
    fields = ['entry_time', 'description', 'amount', 'paid_by', 'notes']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']

class PettyCashAuditInline(admin.TabularInline):
    model = PettyCashAudit
    extra = 0
    readonly_fields = ['action', 'description', 'user', 'timestamp', 'entry']
    can_delete = False

@admin.register(PettyCashDay)
class PettyCashDayAdmin(admin.ModelAdmin):
    list_display = ['entry_date', 'opening_balance', 'total_expenses', 'closing_balance', 'status', 'created_by']
    list_filter = ['status', 'entry_date', 'is_locked']
    search_fields = ['entry_date', 'notes']
    readonly_fields = ['closing_balance', 'total_expenses', 'created_at', 'updated_at', 'approved_at']
    inlines = [PettyCashEntryInline, PettyCashAuditInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('entry_date', 'opening_balance', 'notes')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'is_locked')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Calculated Fields', {
            'fields': ('total_expenses', 'closing_balance'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PettyCashEntry)
class PettyCashEntryAdmin(admin.ModelAdmin):
    list_display = ['petty_cash_day', 'entry_time', 'job_no', 'description', 'amount', 'paid_by', 'created_by']
    list_filter = ['petty_cash_day__entry_date', 'paid_by']
    search_fields = ['job_no', 'description', 'paid_by', 'notes']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    
    fieldsets = (
        ('Entry Information', {
            'fields': ('petty_cash_day', 'entry_time', 'job_no', 'description', 'amount', 'paid_by', 'notes', 'attachment')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PettyCashBalance)
class PettyCashBalanceAdmin(admin.ModelAdmin):
    list_display = ['location', 'currency', 'current_balance', 'last_updated']
    list_filter = ['currency', 'location']
    search_fields = ['location']
    readonly_fields = ['last_updated']

@admin.register(PettyCashAudit)
class PettyCashAuditAdmin(admin.ModelAdmin):
    list_display = ['petty_cash_day', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['description', 'user__username']
    readonly_fields = ['petty_cash_day', 'action', 'description', 'user', 'timestamp', 'entry']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Audit records should only be created by the system
