from django import template
from django.urls import resolve, reverse

register = template.Library()

@register.filter
def truncate_chars(value, length):
    if len(str(value)) > length:
        return str(value)[:length] + '...'
    return value

@register.filter
def status_badge_class(status):
    status = str(status).lower()
    if status in ['approved', 'completed', 'success', 'published']:
        return 'badge-success'
    elif status in ['pending', 'in_progress', 'review']:
        return 'badge-warning'
    elif status in ['rejected', 'failed', 'error']:
        return 'badge-danger'
    elif status in ['draft', 'new']:
        return 'badge-info'
    return 'badge-primary'

@register.simple_tag
def active_nav(request, pattern):
    try:
        url_name = resolve(request.path_info).url_name
        app_name = resolve(request.path_info).app_name
        full_name = f"{app_name}:{url_name}" if app_name else url_name
        if full_name.startswith(pattern):
            return 'active'
    except Exception:
        pass
    return ''

@register.filter
def percentage(value, max_val):
    try:
        return int((float(value) / float(max_val)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
