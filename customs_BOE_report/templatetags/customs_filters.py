from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def calculate_percentage(value, total):
    """Calculates percentage of value from total."""
    try:
        if float(total) > 0:
            return (float(value) / float(total)) * 100
        return 0
    except (ValueError, TypeError):
        return 0