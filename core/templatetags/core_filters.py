from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def smart_number(value):
    """
    Format a number to drop decimal part if it's zero, 
    but preserve true decimal precision (e.g. 0.2000 -> 0.2).
    """
    try:
        if isinstance(value, Decimal):
            d = value.normalize()
            if d == d.to_integral():
                return int(d)
            return round(d, 1)
            
        f_val = float(value)
        if f_val.is_integer():
            return int(f_val)
        return round(f_val, 1)
    except (ValueError, TypeError):
        return value

@register.filter
def abs_val(value):
    """
    Returns the absolute value of a number.
    """
    try:
        return abs(value)
    except TypeError:
        return value
