from django.db import models
from datetime import datetime

class DebitNote(models.Model):
    number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    supplier = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_debit_note_number()
        super().save(*args, **kwargs)

    def generate_debit_note_number(self):
        """Generate debit note number based on year and sequence"""
        today = datetime.now()
        year = today.year
        
        # Find the last debit note for this year
        last_debit_note = DebitNote.objects.filter(
            number__startswith=f"DNR-{year}-"
        ).order_by('-number').first()
        
        if last_debit_note and last_debit_note.number:
            try:
                # Extract the sequence number and increment
                last_sequence = int(last_debit_note.number.split('-')[-1])
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Format: DNR-YYYY-0001
        return f"DNR-{year}-{new_sequence:04d}" 