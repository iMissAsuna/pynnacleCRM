# website/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Allows accessing dictionary items by key in Django templates.
    Usage: {{ my_dict|get_item:my_key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None # Return None if not a dictionary

@register.filter
def replace(value, arg):
    """
    Replaces all occurrences of a substring with another string.
    Usage: {{ value|replace:"old,new" }}
    """
    if not isinstance(value, str):
        return value
    try:
        old, new = arg.split(',', 1)
    except ValueError:
        # If arg does not contain a comma, treat it as replacing arg with empty string
        old = arg
        new = ''
    return value.replace(old, new)

@register.filter
def split(value, arg):
    """
    Splits a string by a given delimiter.
    Usage: {{ value|split:"," }} or {{ value|split:" " }}
    Returns a list of strings.
    """
    if not isinstance(value, str):
        return value
    return value.split(arg)

@register.filter
def div(value, arg):
    """
    Divides the value by the argument. Handles division by zero.
    Usage: {{ value|div:1024 }}
    """
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError):
        return None # Or handle error as appropriate, e.g., return value
    except ZeroDivisionError:
        return 0 # Handle division by zero