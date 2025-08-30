from django.db import models
from django.utils import timezone

class BOETransaction(models.Model):
    declaration_no = models.CharField(max_length=100, verbose_name="Declaration No")
    bill_no = models.CharField(max_length=100, verbose_name="Bill No")
    date = models.DateField(verbose_name="Date")
    hs_code = models.CharField(max_length=50, verbose_name="HS Code")
    particulars = models.CharField(max_length=255, verbose_name="Particulars")
    cog = models.CharField(max_length=100, verbose_name="COG")
    pkg_type = models.CharField(max_length=50, verbose_name="Package Type")
    qty_in = models.IntegerField(default=0, verbose_name="Quantity In")
    wt_in = models.FloatField(default=0.0, verbose_name="Weight In")
    value_in = models.FloatField(default=0.0, verbose_name="Value In")
    qty_out = models.IntegerField(default=0, verbose_name="Quantity Out")
    wt_out = models.FloatField(default=0.0, verbose_name="Weight Out")
    value_out = models.FloatField(default=0.0, verbose_name="Value Out")
    duty = models.FloatField(default=0.0, verbose_name="Duty")
    total_dues = models.FloatField(default=0.0, verbose_name="Total Dues")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customs_boe_transaction'
        verbose_name = 'BOE Transaction'
        verbose_name_plural = 'BOE Transactions'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.declaration_no} - {self.bill_no}"
    
    @property
    def available_qty(self):
        """Calculate available quantity (qty_in - qty_out)"""
        return self.qty_in - self.qty_out
    
    @property
    def available_wt(self):
        """Calculate available weight (wt_in - wt_out)"""
        return self.wt_in - self.wt_out
    
    @property
    def available_value(self):
        """Calculate available value (value_in - value_out)"""
        return self.value_in - self.value_out
    
    @property
    def balance_qty(self):
        """Calculate balance quantity"""
        return self.available_qty
    
    @property
    def balance_wt(self):
        """Calculate balance weight"""
        return self.available_wt
    
    @property
    def balance_value(self):
        """Calculate balance value"""
        return self.available_value
    
    @property
    def duty_percentage(self):
        """Calculate duty at 5%"""
        return self.value_in * 0.05 if self.value_in else 0.0
