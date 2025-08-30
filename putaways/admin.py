from django.contrib import admin
from .models import Putaway

@admin.register(Putaway)
class PutawayAdmin(admin.ModelAdmin):
    list_display = [
        'putaway_number', 
        'grn', 
        'item', 
        'quantity', 
        'pallet_id', 
        'location', 
        'status', 
        'putaway_date', 
        'created_by'
    ]
    list_filter = [
        'status', 
        'putaway_date', 
        'created_at', 
        'location'
    ]
    search_fields = [
        'putaway_number', 
        'grn__grn_number', 
        'item__item_name', 
        'pallet_id', 
        'location__location_name'
    ]
    readonly_fields = [
        'putaway_number', 
        'putaway_date', 
        'created_by', 
        'created_at', 
        'updated_at'
    ]
    date_hierarchy = 'putaway_date'
    ordering = ['-putaway_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('putaway_number', 'grn', 'item', 'quantity', 'pallet_id', 'location')
        }),
        ('Status & Dates', {
            'fields': ('status', 'putaway_date', 'completed_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'remarks'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change) 