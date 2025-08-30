from django import template

register = template.Library()

@register.filter
def replace_underscores(value):
    """
    Replace underscores with spaces in a string.
    Usage: {{ value|replace_underscores }}
    """
    if value is None:
        return ""
    return str(value).replace('_', ' ') 