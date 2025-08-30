from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def template_type_badge(template_type):
    """Convert template type to Bootstrap badge class"""
    badge_classes = {
        'email': 'primary',
        'sms': 'success',
        'whatsapp': 'info',
        'in_app': 'warning',
    }
    return badge_classes.get(template_type, 'secondary')


@register.filter
def activity_color(action):
    """Convert activity action to Bootstrap color class"""
    color_classes = {
        'created': 'success',
        'updated': 'info',
        'deleted': 'danger',
        'activated': 'success',
        'deactivated': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'tested': 'info',
    }
    return color_classes.get(action, 'secondary')


@register.filter
def priority_badge(priority):
    """Convert priority to Bootstrap badge class"""
    badge_classes = {
        'low': 'secondary',
        'normal': 'info',
        'high': 'warning',
        'urgent': 'danger',
    }
    return badge_classes.get(priority, 'secondary')


@register.filter
def status_badge(status):
    """Convert status to Bootstrap badge class"""
    badge_classes = {
        'active': 'success',
        'inactive': 'secondary',
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
    }
    return badge_classes.get(status, 'secondary')


@register.filter
def placeholder_count(template):
    """Get the count of placeholders in a template"""
    if hasattr(template, 'placeholders'):
        return len(template.placeholders) if template.placeholders else 0
    return 0


@register.filter
def truncate_placeholders(placeholders, max_length=50):
    """Truncate placeholder list for display"""
    if not placeholders:
        return "No placeholders"
    
    if len(str(placeholders)) <= max_length:
        return str(placeholders)
    
    return str(placeholders)[:max_length] + "..."


@register.filter
def format_file_size(bytes_value):
    """Format file size in human readable format"""
    if bytes_value is None:
        return "0 B"
    
    try:
        bytes_value = int(bytes_value)
    except (ValueError, TypeError):
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{floatformat(bytes_value, 1)} {unit}"
        bytes_value /= 1024.0
    return f"{floatformat(bytes_value, 1)} TB"


@register.filter
def progress_percentage(current, total):
    """Calculate progress percentage"""
    if not total or total == 0:
        return 0
    
    try:
        percentage = (current / total) * 100
        return min(100, max(0, percentage))
    except (TypeError, ValueError):
        return 0


@register.filter
def template_health_score(template):
    """Calculate a health score for a template based on various factors"""
    score = 100
    
    # Deduct points for missing content
    if not template.content:
        score -= 30
    
    if template.template_type == 'email' and not template.html_content:
        score -= 20
    
    # Deduct points for missing subject
    if not template.subject:
        score -= 10
    
    # Deduct points for inactive status
    if not template.is_active:
        score -= 15
    
    # Deduct points for pending approval
    if template.requires_approval and not template.is_approved:
        score -= 10
    
    # Deduct points for missing placeholders
    if not template.placeholders:
        score -= 15
    
    return max(0, score)


@register.filter
def health_status_class(score):
    """Convert health score to CSS class"""
    if score >= 80:
        return 'success'
    elif score >= 60:
        return 'warning'
    else:
        return 'danger'


@register.filter
def category_color_class(color):
    """Convert category color to Bootstrap color class"""
    color_mapping = {
        'primary': 'primary',
        'secondary': 'secondary',
        'success': 'success',
        'danger': 'danger',
        'warning': 'warning',
        'info': 'info',
        'light': 'light',
        'dark': 'dark',
        'blue': 'primary',
        'green': 'success',
        'red': 'danger',
        'yellow': 'warning',
        'cyan': 'info',
        'gray': 'secondary',
        'purple': 'primary',
        'orange': 'warning',
        'pink': 'info',
    }
    return color_mapping.get(color, 'secondary')
