from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def active_class(context, *view_names):
    request = context['request']
    if request.resolver_match.url_name in view_names:
        return 'active'
    return ''
