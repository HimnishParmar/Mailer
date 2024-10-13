from django import template
import json


register = template.Library()

@register.filter
def filter_by_link_id(link_trackings, link_id):
    return next((lt for lt in link_trackings if lt.link_id == link_id), None)

@register.filter
def is_json(value):
    if isinstance(value, dict):
        return True
    if isinstance(value, str):
        try:
            json.loads(value)
            return True
        except (ValueError, TypeError):
            pass
    return False

