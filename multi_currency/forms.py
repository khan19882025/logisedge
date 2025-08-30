from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Currency, ExchangeRate, CurrencySettings


class CurrencyForm(forms.ModelForm):
    """Form for creating and editing currencies"""
    
    COMMON_CURRENCIES = [
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('JPY', 'JPY - Japanese Yen'),
        ('AUD', 'AUD - Australian Dollar'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('CHF', 'CHF - Swiss Franc'),
        ('CNY', 'CNY - Chinese Yuan'),
        ('AED', 'AED - UAE Dirham'),
        ('SAR', 'SAR - Saudi Riyal'),
        ('QAR', 'QAR - Qatari Riyal'),
        ('KWD', 'KWD - Kuwaiti Dinar'),
        ('BHD', 'BHD - Bahraini Dinar'),
        ('OMR', 'OMR - Omani Rial'),
        ('JOD', 'JOD - Jordanian Dinar'),
        ('EGP', 'EGP - Egyptian Pound'),
        ('TRY', 'TRY - Turkish Lira'),
        ('RUB', 'RUB - Russian Ruble'),
        ('INR', 'INR - Indian Rupee'),
        ('SGD', 'SGD - Singapore Dollar'),
        ('HKD', 'HKD - Hong Kong Dollar'),
        ('NZD', 'NZD - New Zealand Dollar'),
        ('SEK', 'SEK - Swedish Krona'),
        ('NOK', 'NOK - Norwegian Krone'),
        ('DKK', 'DKK - Danish Krone'),
        ('PLN', 'PLN - Polish Zloty'),
        ('CZK', 'CZK - Czech Koruna'),
        ('HUF', 'HUF - Hungarian Forint'),
        ('RON', 'RON - Romanian Leu'),
        ('BGN', 'BGN - Bulgarian Lev'),
        ('HRK', 'HRK - Croatian Kuna'),
        ('RSD', 'RSD - Serbian Dinar'),
        ('UAH', 'UAH - Ukrainian Hryvnia'),
        ('BRL', 'BRL - Brazilian Real'),
        ('MXN', 'MXN - Mexican Peso'),
        ('ARS', 'ARS - Argentine Peso'),
        ('CLP', 'CLP - Chilean Peso'),
        ('COP', 'COP - Colombian Peso'),
        ('PEN', 'PEN - Peruvian Sol'),
        ('UYU', 'UYU - Uruguayan Peso'),
        ('VND', 'VND - Vietnamese Dong'),
        ('THB', 'THB - Thai Baht'),
        ('MYR', 'MYR - Malaysian Ringgit'),
        ('IDR', 'IDR - Indonesian Rupiah'),
        ('PHP', 'PHP - Philippine Peso'),
        ('KRW', 'KRW - South Korean Won'),
        ('TWD', 'TWD - Taiwan Dollar'),
        ('ILS', 'ILS - Israeli Shekel'),
        ('ZAR', 'ZAR - South African Rand'),
        ('NGN', 'NGN - Nigerian Naira'),
        ('KES', 'KES - Kenyan Shilling'),
        ('GHS', 'GHS - Ghanaian Cedi'),
        ('UGX', 'UGX - Ugandan Shilling'),
        ('TZS', 'TZS - Tanzanian Shilling'),
        ('Other', 'Other (Enter manually)'),
    ]

    COMMON_SYMBOLS = [
        ('$', 'US Dollar ($)'),
        ('€', 'Euro (€)'),
        ('£', 'British Pound (£)'),
        ('¥', 'Japanese Yen (¥)'),
        ('₹', 'Indian Rupee (₹)'),
        ('₽', 'Russian Ruble (₽)'),
        ('₩', 'South Korean Won (₩)'),
        ('₺', 'Turkish Lira (₺)'),
        ('₫', 'Vietnamese Dong (₫)'),
        ('₦', 'Nigerian Naira (₦)'),
        ('₱', 'Philippine Peso (₱)'),
        ('₲', 'Paraguayan Guarani (₲)'),
        ('₴', 'Ukrainian Hryvnia (₴)'),
        ('₪', 'Israeli Shekel (₪)'),
        ('₡', 'Costa Rican Colón (₡)'),
        ('₵', 'Ghanaian Cedi (₵)'),
        ('₸', 'Kazakhstani Tenge (₸)'),
        ('د.إ', 'UAE Dirham (د.إ)'),
        ('AED_SVG', 'UAE Dirham (AED) - SVG Icon'),
        ('R$', 'Brazilian Real (R$)'),
        ('A$', 'Australian Dollar (A$)'),
        ('C$', 'Canadian Dollar (C$)'),
        ('S$', 'Singapore Dollar (S$)'),
        ('HK$', 'Hong Kong Dollar (HK$)'),
        ('NZ$', 'New Zealand Dollar (NZ$)'),
        ('kr', 'Swedish Krona (kr)'),
        ('zł', 'Polish Zloty (zł)'),
        ('CHF', 'Swiss Franc (CHF)'),
        ('Kč', 'Czech Koruna (Kč)'),
        ('Ft', 'Hungarian Forint (Ft)'),
        ('R', 'South African Rand (R)'),
        ('Other', 'Other (Enter manually)'),
    ]

    code_select = forms.ChoiceField(
        choices=COMMON_CURRENCIES,
        required=False,
        label='Currency Code',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    name_select = forms.ChoiceField(
        choices=[(choice[1], choice[1]) for choice in COMMON_CURRENCIES if choice[0] != 'Other'] + [('Other', 'Other (Enter manually)')],
        required=False,
        label='Currency Name',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    symbol_select = forms.ChoiceField(
        choices=COMMON_SYMBOLS,
        required=False,
        label='Currency Symbol',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    code = forms.CharField(
        required=True,
        label='Currency Code',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'USD', 'maxlength': '3'})
    )
    
    name = forms.CharField(
        required=True,
        label='Currency Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'US Dollar'})
    )
    
    symbol = forms.CharField(
        required=True,
        label='Currency Symbol',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. $'})
    )

    class Meta:
        model = Currency
        fields = ['code', 'name', 'symbol', 'code_select', 'name_select', 'symbol_select', 'is_base_currency', 'is_active', 'decimal_places']
        widgets = {
            'decimal_places': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '4'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing, pre-select the values if they match common ones
        code_value = self.initial.get('code') or self.instance.code
        name_value = self.initial.get('name') or self.instance.name
        symbol_value = self.initial.get('symbol') or self.instance.symbol
        
        if code_value and code_value in dict(self.COMMON_CURRENCIES):
            self.fields['code_select'].initial = code_value
        else:
            self.fields['code_select'].initial = 'Other'
            
        if name_value:
            # Check if the name matches any of the common currency names
            common_names = [choice[1] for choice in self.COMMON_CURRENCIES if choice[0] != 'Other']
            if name_value in common_names:
                self.fields['name_select'].initial = name_value
            else:
                self.fields['name_select'].initial = 'Other'
        else:
            self.fields['name_select'].initial = 'Other'
            
        if symbol_value:
            # Check if it's the AED SVG path and convert it back to AED_SVG for the form
            if symbol_value == 'static/img/aed_currency.svg':
                self.fields['symbol_select'].initial = 'AED_SVG'
            elif symbol_value in dict(self.COMMON_SYMBOLS):
                self.fields['symbol_select'].initial = symbol_value
            else:
                self.fields['symbol_select'].initial = 'Other'
        else:
            self.fields['symbol_select'].initial = 'Other'

    def clean(self):
        cleaned_data = super().clean()
        
        # Handle code selection
        code_select = cleaned_data.get('code_select')
        code = cleaned_data.get('code')
        if code_select and code_select != 'Other':
            cleaned_data['code'] = code_select
            # Extract name from the selected currency
            currency_name = dict(self.COMMON_CURRENCIES).get(code_select, '').split(' - ', 1)[-1]
            cleaned_data['name'] = currency_name
        
        # Handle name selection
        name_select = cleaned_data.get('name_select')
        name = cleaned_data.get('name')
        if name_select and name_select != 'Other':
            cleaned_data['name'] = name_select
            # Find the corresponding code for the selected name
            for code_choice, name_choice in self.COMMON_CURRENCIES:
                if name_choice == name_select:
                    cleaned_data['code'] = code_choice
                    break
        
        # Handle symbol selection
        symbol_select = cleaned_data.get('symbol_select')
        symbol = cleaned_data.get('symbol')
        if symbol_select and symbol_select != 'Other':
            if symbol_select == 'AED_SVG':
                # Convert AED_SVG to the actual SVG file path
                cleaned_data['symbol'] = 'static/img/aed_currency.svg'
            else:
                cleaned_data['symbol'] = symbol_select
        
        # Validation - ensure we have the required fields
        final_code = cleaned_data.get('code')
        final_name = cleaned_data.get('name')
        final_symbol = cleaned_data.get('symbol')
        
        if not final_code:
            self.add_error('code', 'Currency code is required')
        if not final_name:
            self.add_error('name', 'Currency name is required')
        if not final_symbol:
            self.add_error('symbol', 'Currency symbol is required')
            
        return cleaned_data


class ExchangeRateForm(forms.ModelForm):
    """Form for creating and editing exchange rates"""
    
    class Meta:
        model = ExchangeRate
        fields = ['from_currency', 'to_currency', 'rate', 'rate_type', 'effective_date', 'expiry_date', 'is_active', 'notes']
        widgets = {
            'from_currency': forms.Select(attrs={'class': 'form-control'}),
            'to_currency': forms.Select(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'min': '0.000001'
            }),
            'rate_type': forms.Select(attrs={'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Additional notes about this exchange rate...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        from_currency = cleaned_data.get('from_currency')
        to_currency = cleaned_data.get('to_currency')
        effective_date = cleaned_data.get('effective_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if from_currency and to_currency and from_currency == to_currency:
            raise ValidationError("From and To currencies cannot be the same")
        
        if effective_date and expiry_date and effective_date > expiry_date:
            raise ValidationError("Expiry date must be after effective date")
        
        if effective_date and effective_date < timezone.now().date():
            raise ValidationError("Effective date cannot be in the past")
        
        return cleaned_data


class CurrencySettingsForm(forms.ModelForm):
    """Form for currency settings"""
    
    class Meta:
        model = CurrencySettings
        fields = ['default_currency', 'auto_update_rates', 'api_provider', 'api_key', 'update_frequency']
        widgets = {
            'default_currency': forms.Select(attrs={'class': 'form-control'}),
            'api_provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., exchangerate-api.com'
            }),
            'api_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your API key'
            }),
            'update_frequency': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active currencies in the dropdown
        self.fields['default_currency'].queryset = Currency.objects.filter(is_active=True)


class CurrencySearchForm(forms.Form):
    """Form for searching currencies"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by code, name, or symbol...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Currency.CURRENCY_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_base_currency = forms.BooleanField(
        required=False,
        label='Base Currency Only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ExchangeRateSearchForm(forms.Form):
    """Form for searching exchange rates"""
    
    from_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        empty_label="All From Currencies",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    to_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        empty_label="All To Currencies",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    rate_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ExchangeRate.RATE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    effective_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    effective_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        label='Active Rates Only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    ) 