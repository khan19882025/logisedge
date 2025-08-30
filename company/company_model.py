from django.db import models
from django.utils import timezone

class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name="Company Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Company Code")
    address = models.TextField(verbose_name="Address")
    phone = models.CharField(max_length=20, verbose_name="Phone")
    email = models.EmailField(verbose_name="Email")
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    tax_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tax Number")
    registration_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Registration Number")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name="Logo")
    
    # Bank Details for Invoice Display
    bank_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Bank Name")
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Bank Account Number")
    bank_iban = models.CharField(max_length=50, blank=True, null=True, verbose_name="IBAN")
    bank_swift_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="SWIFT/BIC Code")
    bank_branch = models.CharField(max_length=200, blank=True, null=True, verbose_name="Bank Branch")
    
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @property
    def has_bank_details(self):
        """Check if company has bank details filled"""
        return bool(self.bank_name and self.bank_account_number)
    
    @property
    def bank_details_display(self):
        """Return formatted bank details for display"""
        if not self.has_bank_details:
            return ""
        
        details = []
        if self.bank_name:
            details.append(f"Bank: {self.bank_name}")
        if self.bank_account_number:
            details.append(f"Account: {self.bank_account_number}")
        if self.bank_iban:
            details.append(f"IBAN: {self.bank_iban}")
        if self.bank_swift_code:
            details.append(f"SWIFT: {self.bank_swift_code}")
        if self.bank_branch:
            details.append(f"Branch: {self.bank_branch}")
        
        return " | ".join(details) 