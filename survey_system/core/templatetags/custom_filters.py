from django import template
from operator import attrgetter
import itertools
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def groupby_attr(queryset, attr):
    """Группировка объектов по атрибуту в шаблоне Django."""
    sorted_qs = sorted(queryset, key=attrgetter(attr))
    return [(key, list(group)) for key, group in itertools.groupby(sorted_qs, key=attrgetter(attr))]