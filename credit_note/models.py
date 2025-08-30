from django.db import models
from datetime import datetime

class CreditNote(models.Model):
    number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    customer = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_credit_note_number()
        super().save(*args, **kwargs)

    def generate_credit_note_number(self):
        """Generate credit note number based on year and sequence"""
        today = datetime.now()
        year = today.year
        
        # Find the last credit note for this year
        last_credit_note = CreditNote.objects.filter(
            number__startswith=f"CNR-{year}-"
        ).order_by('-number').first()
        
        if last_credit_note and last_credit_note.number:
            try:
                # Extract the sequence number and increment
                last_sequence = int(last_credit_note.number.split('-')[-1])
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Format: CNR-YYYY-0001
        return f"CNR-{year}-{new_sequence:04d}" 