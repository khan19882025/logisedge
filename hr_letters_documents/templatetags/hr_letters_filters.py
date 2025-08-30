from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import datetime, timedelta

register = template.Library()


@register.filter
def status_badge(status):
    """Return appropriate Bootstrap badge class for letter status"""
    status_classes = {
        'draft': 'warning',
        'finalized': 'info',
        'signed': 'success',
        'issued': 'primary',
    }
    return status_classes.get(status, 'secondary')


@register.filter
def file_size_format(bytes_value):
    """Format file size in human readable format"""
    if not bytes_value:
        return '0 B'
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


@register.filter
def time_since(value):
    """Return time since a datetime value"""
    if not value:
        return ''
    
    now = timezone.now()
    diff = now - value
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


@register.filter
def truncate_text(text, length=100):
    """Truncate text to specified length"""
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length] + '...'


@register.filter
def file_type_icon(file_type):
    """Return appropriate icon for file type"""
    icon_map = {
        '.pdf': 'fas fa-file-pdf',
        '.doc': 'fas fa-file-word',
        '.docx': 'fas fa-file-word',
        '.xls': 'fas fa-file-excel',
        '.xlsx': 'fas fa-file-excel',
        '.ppt': 'fas fa-file-powerpoint',
        '.pptx': 'fas fa-file-powerpoint',
        '.txt': 'fas fa-file-alt',
        '.jpg': 'fas fa-file-image',
        '.jpeg': 'fas fa-file-image',
        '.png': 'fas fa-file-image',
        '.gif': 'fas fa-file-image',
    }
    
    return icon_map.get(file_type.lower(), 'fas fa-file')


@register.filter
def is_recent(date_value, days=7):
    """Check if a date is within recent days"""
    if not date_value:
        return False
    
    now = timezone.now().date()
    return (now - date_value).days <= days


@register.filter
def language_display(language_code):
    """Display language name from code"""
    language_map = {
        'en': 'English',
        'ar': 'Arabic',
        'both': 'English & Arabic',
    }
    return language_map.get(language_code, language_code)


@register.filter
def approval_status_badge(status):
    """Return appropriate badge class for approval status"""
    status_classes = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
    }
    return status_classes.get(status, 'secondary')


@register.filter
def action_icon(action):
    """Return appropriate icon for letter action"""
    icon_map = {
        'created': 'fas fa-plus',
        'updated': 'fas fa-edit',
        'finalized': 'fas fa-check-circle',
        'signed': 'fas fa-signature',
        'issued': 'fas fa-paper-plane',
        'approved': 'fas fa-thumbs-up',
        'rejected': 'fas fa-thumbs-down',
    }
    return icon_map.get(action, 'fas fa-circle')


@register.filter
def action_color(action):
    """Return appropriate color for letter action"""
    color_map = {
        'created': 'primary',
        'updated': 'info',
        'finalized': 'success',
        'signed': 'success',
        'issued': 'primary',
        'approved': 'success',
        'rejected': 'danger',
    }
    return color_map.get(action, 'secondary')


@register.filter
def format_currency(amount, currency='AED'):
    """Format currency amount"""
    if not amount:
        return f'0 {currency}'
    
    try:
        return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return f'0 {currency}'


@register.filter
def format_date(date_value, format_string='M d, Y'):
    """Format date with custom format"""
    if not date_value:
        return ''
    
    try:
        return date_value.strftime(format_string)
    except AttributeError:
        return ''


@register.filter
def is_urgent(letter):
    """Check if a letter is urgent (draft for more than 3 days)"""
    if not letter or letter.status != 'draft':
        return False
    
    now = timezone.now().date()
    return (now - letter.created_at.date()).days > 3


@register.filter
def letter_type_count(letter_type):
    """Get count of letters for a letter type"""
    return letter_type.generatedletter_set.count()


@register.filter
def document_count(category):
    """Get count of documents for a category"""
    return category.documents.count()


@register.filter
def is_public_badge(is_public):
    """Return badge class for public/private status"""
    return 'success' if is_public else 'secondary'


@register.filter
def is_active_badge(is_active):
    """Return badge class for active/inactive status"""
    return 'success' if is_active else 'danger'


@register.simple_tag
def get_letter_statistics():
    """Get letter statistics for dashboard"""
    from hr_letters_documents.models import GeneratedLetter
    
    total = GeneratedLetter.objects.count()
    draft = GeneratedLetter.objects.filter(status='draft').count()
    finalized = GeneratedLetter.objects.filter(status='finalized').count()
    signed = GeneratedLetter.objects.filter(status='signed').count()
    
    return {
        'total': total,
        'draft': draft,
        'finalized': finalized,
        'signed': signed,
    }


@register.simple_tag
def get_recent_activity(limit=5):
    """Get recent letter activity"""
    from hr_letters_documents.models import LetterHistory
    
    return LetterHistory.objects.select_related('letter', 'user').order_by('-timestamp')[:limit] 