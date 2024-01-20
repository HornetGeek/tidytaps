from django import template

register = template.Library()

@register.filter(name='split_static')
def split_static(value):
    return value.split("static")