# coding: utf-8

from django.utils.encoding import force_text


def replace_from_choices(choices):
    def inner(value):
        return force_text(choices.get(value, value), strings_only=True)
    return inner


def build_update_functions(fields):
    update_functions = []

    for field_index, field in enumerate(fields):
        if field.choices:
            choices = dict(field.flatchoices)
            update_functions.append((field_index,
                                     replace_from_choices(choices)))

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
