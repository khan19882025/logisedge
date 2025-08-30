from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key)


@register.filter
def category_color(category):
    """Get color class for account category"""
    colors = {
        'ASSET': 'primary',
        'LIABILITY': 'danger', 
        'EQUITY': 'success',
        'REVENUE': 'info',
        'EXPENSE': 'warning'
    }
    return colors.get(category, 'secondary')


@register.filter
def account_nature_icon(nature):
    """Get icon for account nature"""
    icons = {
        'DEBIT': 'bi-arrow-down-circle',
        'CREDIT': 'bi-arrow-up-circle',
        'BOTH': 'bi-arrow-left-right'
    }
    return icons.get(nature, 'bi-question-circle')


@register.filter
def format_balance(balance):
    """Format balance with proper sign and color"""
    if balance is None:
        return '0.00'
    
    formatted = f"{float(balance):,.2f}"
    if float(balance) < 0:
        return f"({formatted})"
    return formatted


@register.filter
def balance_color(balance):
    """Get color class for balance"""
    if balance is None:
        return 'secondary'
    
    if float(balance) >= 0:
        return 'success'
    return 'danger' 