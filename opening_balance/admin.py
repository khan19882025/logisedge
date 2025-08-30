from django.contrib import admin
from .models import OpeningBalance, OpeningBalanceEntry


class OpeningBalanceEntryInline(admin.TabularInline):
    model = OpeningBalanceEntry
    extra = 1
    fields = ('account', 'amount', 'balance_type', 'remarks')


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(admin.ModelAdmin):
    list_display = ('financial_year', 'created_at', 'total_debit', 'total_credit', 'is_balanced')
    list_filter = ('financial_year', 'created_at')
    search_fields = ('financial_year__name',)
    readonly_fields = ('total_debit', 'total_credit', 'is_balanced', 'created_at', 'updated_at')
    inlines = [OpeningBalanceEntryInline]
    
    def total_debit(self, obj):
        return sum(entry.amount for entry in obj.entries.filter(balance_type='debit'))
    total_debit.short_description = 'Total Debit'
    
    def total_credit(self, obj):
        return sum(entry.amount for entry in obj.entries.filter(balance_type='credit'))
    total_credit.short_description = 'Total Credit'
    
    def is_balanced(self, obj):
        total_debit = sum(entry.amount for entry in obj.entries.filter(balance_type='debit'))
        total_credit = sum(entry.amount for entry in obj.entries.filter(balance_type='credit'))
        return total_debit == total_credit
    is_balanced.boolean = True
    is_balanced.short_description = 'Balanced'


@admin.register(OpeningBalanceEntry)
class OpeningBalanceEntryAdmin(admin.ModelAdmin):
    list_display = ('opening_balance', 'account', 'amount', 'balance_type', 'remarks')
    list_filter = ('balance_type', 'account__account_type')
    search_fields = ('account__account_name', 'account__account_code', 'remarks') 