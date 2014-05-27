# coding: utf-8

from django.core.cache import cache
from django.utils.encoding import force_text


def replace_from_choices(choices):
    def inner(values):
        return [choices.get(v, v) for v in values]
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

    def get_cache_key_from_pk(pk):
        return None if pk is None else base_cache_key % pk

    def inner(pk_series):
        pk_series = pk_series.where(pk_series.notnull(), None)
        cache_keys = pk_series.apply(
            get_cache_key_from_pk, convert_dtype=False)
        unique_cache_keys = list(filter(None, cache_keys.unique()))

        if not unique_cache_keys:
            return pk_series

        out_dict = cache.get_many(unique_cache_keys)

        if len(out_dict) < len(unique_cache_keys):
            out_dict = {base_cache_key % obj.pk: force_text(obj)
                        for obj in model.objects.filter(
                            pk__in=list(filter(None, pk_series.unique())))}
            cache.set_many(out_dict)

        return list(map(out_dict.get, cache_keys))

    return inner


def build_update_functions(fieldnames, fields):
    for fieldname, field in zip(fieldnames, fields):
        if field.choices:
            choices = {k: force_text(v)
                       for k, v in field.flatchoices}
            yield fieldname, replace_from_choices(choices)

        elif field.get_internal_type() == 'ForeignKey':
            yield fieldname, replace_pk(field.rel.to)


def update_with_verbose(df, fieldnames, fields):
    for fieldname, function in build_update_functions(fieldnames, fields):
        df[fieldname] = function(df[fieldname])
