# coding: utf-8

from django.core.cache import cache
from django.utils.encoding import force_text


def replace_from_choices(choices):
    def inner(value):
        return force_text(choices.get(value, value), strings_only=True)
    return inner


def get_base_cache_key(model):
    return 'pandas_%s_%s_%%d_rendering' % (
        model._meta.app_label, model._meta.module_name)


def get_cache_key(obj):
    return get_base_cache_key(obj._meta.model) % obj.pk


def invalidate(obj):
    cache.delete(get_cache_key(obj))


def invalidate_signal_handler(sender, **kwargs):
    invalidate(kwargs['instance'])


def replace_pk(model):
    base_cache_key = get_base_cache_key(model)

    def inner(pk):
        if pk is None:
            return
        cache_key = base_cache_key % pk
        out = cache.get(cache_key, None)
        if out is None:
            out = force_text(model.objects.get(pk=pk))
            cache.set(cache_key, out)
        return out

    return inner


def build_update_functions(fields):
    update_functions = []

    for field_index, field in enumerate(fields):
        if field.choices:
            choices = dict(field.flatchoices)
            update_functions.append((field_index,
                                     replace_from_choices(choices)))

        if field.get_internal_type() == 'ForeignKey':
            update_functions.append((field_index, replace_pk(field.rel.to)))

    return update_functions


def update_with_verbose(values_list, fields):
    update_functions = build_update_functions(fields)

    if not update_functions:
        return

    for line_index, line in enumerate(values_list):
        line = list(line)
        values_list[line_index] = line
        for field_index, function in update_functions:
            line[field_index] = function(line[field_index])
