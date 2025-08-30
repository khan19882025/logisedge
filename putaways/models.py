from django.db import models
from django.contrib.auth.models import User
from grn.models import GRN, GRNItem
from items.models import Item
from facility.models import FacilityLocation

class Putaway(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    putaway_number = models.CharField(max_length=50, unique=True, verbose_name="Putaway Number")
    grn = models.ForeignKey(GRN, on_delete=models.CASCADE, verbose_name="GRN")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    pallet_id = models.CharField(max_length=100, verbose_name="Pallet ID")
    location = models.ForeignKey(FacilityLocation, on_delete=models.CASCADE, verbose_name="Location")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    putaway_date = models.DateTimeField(auto_now_add=True, verbose_name="Putaway Date")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Completed Date")
    
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='putaways_created', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Putaway"
        verbose_name_plural = "Putaways"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Putaway {self.putaway_number} - {self.item.item_name}"
    
    def save(self, *args, **kwargs):
        if not self.putaway_number:
            # Generate putaway number
            last_putaway = Putaway.objects.order_by('-id').first()
            if last_putaway:
                last_number = int(last_putaway.putaway_number.split('-')[1])
                self.putaway_number = f"PTW-{last_number + 1:06d}"
            else:
                self.putaway_number = "PTW-000001"
        super().save(*args, **kwargs) 