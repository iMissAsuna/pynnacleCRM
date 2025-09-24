# your_project_name/website/templatetags/website_filters.py

import os
from django import template

register = template.Library()

@register.filter
def sum_media_count(sub_categories):
    """
    Calculates the total count of media items within a list of sub-categories.
    Usage: {{ sub_categories_list|sum_media_count }}
    """
    total = 0
    if isinstance(sub_categories, list):
        for sub_cat in sub_categories:
            if 'media_list' in sub_cat and isinstance(sub_cat['media_list'], list):
                total += len(sub_cat['media_list'])
    return total

@register.filter(name='get_item') # Using name='get_item' for clarity, though optional here
def get_item(dictionary, key):
    """
    Allows dictionary item access in Django templates.
    Usage: {{ my_dictionary|get_item:key_variable }}
    """
    return dictionary.get(key)

@register.filter
def basename(value):
    """Returns the base filename from a full path."""
    if value:
        return os.path.basename(value)
    return ""