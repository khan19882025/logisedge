from django import template

register = template.Library()


@register.filter
def status_badge(status):
    """Return the appropriate badge class for grievance status"""
    badge_map = {
        'new': 'new',
        'under_review': 'under_review',
        'investigating': 'investigating',
        'resolved': 'resolved',
        'closed': 'closed',
        'escalated': 'escalated',
    }
    return badge_map.get(status, 'secondary')


@register.filter
def priority_badge(priority):
    """Return the appropriate badge class for priority"""
    badge_map = {
        'low': 'low',
        'medium': 'medium',
        'high': 'high',
        'urgent': 'urgent',
    }
    return badge_map.get(priority, 'secondary')


@register.filter
def severity_badge(severity):
    """Return the appropriate badge class for severity"""
    badge_map = {
        'minor': 'minor',
        'moderate': 'moderate',
        'major': 'major',
        'critical': 'critical',
    }
    return badge_map.get(severity, 'secondary')


@register.filter
def case_status_badge(status):
    """Return the appropriate badge class for disciplinary case status"""
    badge_map = {
        'open': 'open',
        'investigating': 'investigating',
        'hearing_scheduled': 'hearing_scheduled',
        'hearing_completed': 'hearing_completed',
        'decision_pending': 'decision_pending',
        'action_taken': 'action_taken',
        'closed': 'closed',
        'appealed': 'appealed',
    }
    return badge_map.get(status, 'secondary')


@register.filter
def action_status_badge(status):
    """Return the appropriate badge class for disciplinary action status"""
    badge_map = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'implemented': 'info',
    }
    return badge_map.get(status, 'secondary')


@register.filter
def appeal_status_badge(status):
    """Return the appropriate badge class for appeal status"""
    badge_map = {
        'pending': 'warning',
        'under_review': 'info',
        'approved': 'success',
        'rejected': 'danger',
        'withdrawn': 'secondary',
    }
    return badge_map.get(status, 'secondary')


@register.filter
def format_duration(days):
    """Format duration in days to a readable string"""
    if not days:
        return "N/A"
    
    if days == 1:
        return "1 day"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        remaining_days = days % 7
        if remaining_days == 0:
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            return f"{weeks} week{'s' if weeks > 1 else ''}, {remaining_days} day{'s' if remaining_days > 1 else ''}"
    else:
        months = days // 30
        remaining_days = days % 30
        if remaining_days == 0:
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            return f"{months} month{'s' if months > 1 else ''}, {remaining_days} day{'s' if remaining_days > 1 else ''}"


@register.filter
def time_since(date):
    """Return a human-readable time since the given date"""
    from django.utils import timezone
    from datetime import timedelta
    
    if not date:
        return "N/A"
    
    now = timezone.now()
    diff = now - date
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = (diff.seconds % 3600) // 60
            if minutes > 0:
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"


@register.filter
def truncate_words(text, limit=50):
    """Truncate text to a specific number of words"""
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= limit:
        return text
    
    return " ".join(words[:limit]) + "..."


@register.filter
def file_size_format(bytes_size):
    """Format file size in human-readable format"""
    if not bytes_size:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    
    return f"{bytes_size:.1f} TB"


@register.filter
def get_file_extension(filename):
    """Get file extension from filename"""
    if not filename:
        return ""
    
    return filename.split('.')[-1].lower() if '.' in filename else ""


@register.filter
def is_image_file(filename):
    """Check if file is an image based on extension"""
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
    extension = get_file_extension(filename)
    return extension in image_extensions


@register.filter
def is_pdf_file(filename):
    """Check if file is a PDF based on extension"""
    return get_file_extension(filename) == 'pdf'


@register.filter
def is_document_file(filename):
    """Check if file is a document based on extension"""
    document_extensions = ['doc', 'docx', 'pdf', 'txt', 'rtf']
    extension = get_file_extension(filename)
    return extension in document_extensions 