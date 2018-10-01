from django import template

register = template.Library()

@register.filter
def get_at_index(list, index):
    return list[index]

@register.assignment_tag
def is_development():
    from MainAPP.models import SiteSettings
    SETTINGS=SiteSettings.load()
    return SETTINGS.VERSION_DEVELOPER==True