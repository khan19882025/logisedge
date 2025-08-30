from django import template

register = template.Library()

@register.filter
def status_badge(status):
    """
    Returns Bootstrap badge class based on backup execution status
    """
    status_mapping = {
        'pending': 'secondary',
        'running': 'info',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'warning',
    }

    return status_mapping.get(status.lower(), 'secondary')

@register.filter
def status_badge_color(status):
    """
    Returns Bootstrap color class based on backup execution status
    """
    status_mapping = {
        'pending': 'secondary',
        'running': 'info',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'warning',
    }

    return status_mapping.get(status.lower(), 'secondary')

@register.filter
def log_level_border(level):
    """
    Returns Bootstrap border color class based on log level
    """
    level_mapping = {
        'info': 'info',
        'warning': 'warning',
        'error': 'danger',
        'critical': 'danger',
    }

    return level_mapping.get(level.lower(), 'secondary')

@register.filter
def log_level_badge(level):
    """
    Returns Bootstrap badge class based on log level
    """
    level_mapping = {
        'info': 'info',
        'warning': 'warning',
        'error': 'danger',
        'critical': 'danger',
    }

    return level_mapping.get(level.lower(), 'secondary')

@register.filter
def div(value, arg):
    """
    Divides the value by the argument
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
