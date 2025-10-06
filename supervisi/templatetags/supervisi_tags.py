from django import template

register = template.Library()

@register.filter
def sum_aspek(items):
    total = 0
    for i in items:
        # pastikan related_name 'aspek' ada di model ItemFormat
        if hasattr(i, 'aspek'):
            total += i.aspek.count()
    return total

# supervisi_tags.py
from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})
