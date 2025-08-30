from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def status_color(status):
    """
    Returns a Bootstrap color class for a given quotation status.
    """
    return {
        'draft': 'secondary',
        'sent': 'primary',
        'accepted': 'success',
        'rejected': 'danger',
        'expired': 'warning',
    }.get(status, 'secondary')

@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument.
    Used for VAT calculations.
    """
    try:
        # Convert to Decimal for proper decimal arithmetic
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
            
        if isinstance(arg, str):
            arg = Decimal(arg)
        elif not isinstance(arg, Decimal):
            arg = Decimal(str(arg))
            
        return value * arg
    except (ValueError, TypeError):
        return Decimal('0') 