from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def status_badge_color(status):
    """Return the appropriate badge color class for a status"""
    color_map = {
        'at_origin_port': 'secondary',
        'sailing': 'info',
        'arrived_destination': 'warning',
        'customs_cleared': 'success',
        'delivered': 'success',
        'on_hold': 'warning',
        'damaged': 'danger',
        'returned': 'dark',
    }
    return color_map.get(status, 'secondary')

@register.filter
def status_display(status):
    """Return the human-readable status name"""
    status_map = {
        'at_origin_port': 'At Origin Port',
        'sailing': 'Sailing',
        'arrived_destination': 'Arrived at Destination',
        'customs_cleared': 'Customs Cleared',
        'delivered': 'Delivered',
        'on_hold': 'On Hold',
        'damaged': 'Damaged',
        'returned': 'Returned',
    }
    return status_map.get(status, status)

@register.filter
def format_duration(start_date, end_date):
    """Format the duration between two dates"""
    if not start_date or not end_date:
        return "N/A"
    
    delta = end_date - start_date
    days = delta.days
    
    if days == 0:
        return "Same day"
    elif days == 1:
        return "1 day"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''}"
    else:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''}"

@register.filter
def is_delayed(shipment):
    """Check if a shipment is delayed"""
    if shipment.expected_arrival and shipment.actual_arrival:
        return shipment.actual_arrival > shipment.expected_arrival
    return False

@register.filter
def delay_days(shipment):
    """Calculate delay in days"""
    if shipment.expected_arrival and shipment.actual_arrival:
        delta = shipment.actual_arrival - shipment.expected_arrival
        return delta.days
    return 0

@register.filter
def format_weight(weight):
    """Format weight with appropriate units"""
    if not weight:
        return "N/A"
    
    if weight >= 1000:
        return f"{floatformat(weight/1000, 1)} tons"
    else:
        return f"{floatformat(weight, 1)} kg"

@register.filter
def format_volume(volume):
    """Format volume with appropriate units"""
    if not volume:
        return "N/A"
    
    if volume >= 1000:
        return f"{floatformat(volume/1000, 1)} m³"
    else:
        return f"{floatformat(volume, 1)} L"

@register.filter
def truncate_text(text, length=50):
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    return text[:length] + "..."

@register.filter
def highlight_search(text, search_term):
    """Highlight search terms in text"""
    if not text or not search_term:
        return text
    
    import re
    pattern = re.compile(f'({re.escape(search_term)})', re.IGNORECASE)
    return pattern.sub(r'<span class="highlight">\1</span>', str(text))

@register.filter
def file_size_display(size_bytes):
    """Convert bytes to human readable format"""
    if not size_bytes:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{floatformat(size_bytes, 1)} {unit}"
        size_bytes /= 1024.0
    
    return f"{floatformat(size_bytes, 1)} TB"

@register.filter
def notification_status_icon(notification):
    """Return appropriate icon for notification status"""
    if notification.is_delivered:
        return "fas fa-check-circle text-success"
    elif notification.is_sent:
        return "fas fa-paper-plane text-info"
    else:
        return "fas fa-exclamation-triangle text-warning"

@register.filter
def attachment_type_icon(file_type):
    """Return appropriate icon for attachment type"""
    icon_map = {
        'pod': 'fas fa-file-signature',
        'photo': 'fas fa-camera',
        'gate_pass': 'fas fa-id-card',
        'customs_doc': 'fas fa-file-contract',
        'invoice': 'fas fa-file-invoice',
        'packing_list': 'fas fa-list',
        'other': 'fas fa-file',
    }
    return icon_map.get(file_type, 'fas fa-file')

@register.filter
def progress_percentage(shipment):
    """Calculate progress percentage based on status"""
    progress_map = {
        'at_origin_port': 10,
        'sailing': 30,
        'arrived_destination': 60,
        'customs_cleared': 80,
        'delivered': 100,
        'on_hold': 50,
        'damaged': 0,
        'returned': 0,
    }
    return progress_map.get(shipment.current_status, 0)
