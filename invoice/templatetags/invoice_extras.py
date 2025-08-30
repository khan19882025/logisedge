from django import template

register = template.Library()

@register.filter
def service_name_only(value):
    """
    Extract only the service name part from a description like "WAR0001 - Handling in"
    Returns "Handling in" instead of "WAR0001 - Handling in"
    """
    if not value:
        return "-"
    
    value_str = str(value)
    if " - " in value_str:
        return value_str.split(" - ", 1)[1]
    else:
        return value_str

@register.filter
def number_to_words(value):
    """
    Convert a number to its word representation
    Example: 1234.56 -> "One Thousand Two Hundred Thirty-Four and 56/100"
    """
    if value is None:
        return "Zero"
    
    try:
        # Convert to float and handle decimal parts
        num = float(value)
        if num == 0:
            return "Zero"
        
        # Split into integer and decimal parts
        integer_part = int(num)
        decimal_part = round((num - integer_part) * 100)
        
        # Convert integer part to words
        if integer_part == 0:
            integer_words = ""
        else:
            integer_words = _convert_integer_to_words(integer_part)
        
        # Convert decimal part to words
        if decimal_part == 0:
            decimal_words = ""
        else:
            decimal_words = f" and {decimal_part}/100"
        
        # Combine parts
        if integer_words and decimal_words:
            result = integer_words + decimal_words
        elif integer_words:
            result = integer_words
        else:
            result = decimal_words
        
        return result.strip()
        
    except (ValueError, TypeError):
        return "Invalid Number"

def _convert_integer_to_words(n):
    """Helper function to convert integer to words"""
    if n == 0:
        return ""
    
    # Define word mappings
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    if n < 10:
        return ones[n]
    elif n < 20:
        return teens[n - 10]
    elif n < 100:
        if n % 10 == 0:
            return tens[n // 10]
        else:
            return tens[n // 10] + "-" + ones[n % 10]
    elif n < 1000:
        if n % 100 == 0:
            return ones[n // 100] + " Hundred"
        else:
            return ones[n // 100] + " Hundred " + _convert_integer_to_words(n % 100)
    elif n < 1000000:
        if n % 1000 == 0:
            return _convert_integer_to_words(n // 1000) + " Thousand"
        else:
            return _convert_integer_to_words(n // 1000) + " Thousand " + _convert_integer_to_words(n % 1000)
    elif n < 1000000000:
        if n % 1000000 == 0:
            return _convert_integer_to_words(n // 1000000) + " Million"
        else:
            return _convert_integer_to_words(n // 1000000) + " Million " + _convert_integer_to_words(n % 1000000)
    else:
        if n % 1000000000 == 0:
            return _convert_integer_to_words(n // 1000000000) + " Billion"
        else:
            return _convert_integer_to_words(n // 1000000000) + " Billion " + _convert_integer_to_words(n % 1000000000) 