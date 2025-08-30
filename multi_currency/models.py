from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Currency(models.Model):
    """Model for storing currency information"""
    
    CURRENCY_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 currency code (e.g., USD, EUR, AED)")
    name = models.CharField(max_length=100, help_text="Full currency name (e.g., US Dollar, Euro, UAE Dirham)")
    symbol = models.CharField(max_length=10, help_text="Currency symbol (e.g., $, €, د.إ)")
    is_base_currency = models.BooleanField(default=False, help_text="Mark as base currency for the system")
    is_active = models.BooleanField(default=True, help_text="Whether this currency is active for transactions")
    decimal_places = models.PositiveIntegerField(default=2, help_text="Number of decimal places for this currency")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one base currency exists
        if self.is_base_currency:
            Currency.objects.filter(is_base_currency=True).update(is_base_currency=False)
        super().save(*args, **kwargs)


class ExchangeRate(models.Model):
    """Model for storing exchange rates between currencies"""
    
    RATE_TYPE_CHOICES = [
        ('manual', 'Manual'),
        ('api', 'API'),
        ('auto', 'Auto'),
    ]
    
    from_currency = models.ForeignKey(
        Currency, 
        on_delete=models.CASCADE, 
        related_name='exchange_rates_from',
        help_text="Source currency"
    )
    to_currency = models.ForeignKey(
        Currency, 
        on_delete=models.CASCADE, 
        related_name='exchange_rates_to',
        help_text="Target currency"
    )
    rate = models.DecimalField(
        max_digits=15, 
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="Exchange rate (1 from_currency = rate to_currency)"
    )
    rate_type = models.CharField(
        max_length=10, 
        choices=RATE_TYPE_CHOICES, 
        default='manual',
        help_text="How this rate was obtained"
    )
    effective_date = models.DateField(help_text="Date when this rate becomes effective")
    expiry_date = models.DateField(null=True, blank=True, help_text="Date when this rate expires (optional)")
    is_active = models.BooleanField(default=True, help_text="Whether this rate is currently active")
    notes = models.TextField(blank=True, help_text="Additional notes about this rate")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        unique_together = ['from_currency', 'to_currency', 'effective_date']
        ordering = ['-effective_date', 'from_currency', 'to_currency']
    
    def __str__(self):
        return f"{self.from_currency.code} to {self.to_currency.code}: {self.rate} (Effective: {self.effective_date})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.from_currency == self.to_currency:
            raise ValidationError("From and To currencies cannot be the same")
        if self.expiry_date and self.effective_date > self.expiry_date:
            raise ValidationError("Expiry date must be after effective date")


class CurrencySettings(models.Model):
    """Model for storing global currency settings"""
    
    default_currency = models.ForeignKey(
        Currency, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_for_settings',
        help_text="Default currency for the system"
    )
    auto_update_rates = models.BooleanField(
        default=False, 
        help_text="Automatically update exchange rates from API"
    )
    api_provider = models.CharField(
        max_length=50, 
        blank=True,
        help_text="API provider for exchange rates (e.g., exchangerate-api.com)"
    )
    api_key = models.CharField(
        max_length=255, 
        blank=True,
        help_text="API key for exchange rate service"
    )
    update_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily',
        help_text="How often to update exchange rates"
    )
    last_update = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Currency Settings"
        verbose_name_plural = "Currency Settings"
    
    def __str__(self):
        return f"Currency Settings - Default: {self.default_currency.code if self.default_currency else 'Not Set'}" 