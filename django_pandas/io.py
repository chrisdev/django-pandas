import pandas as pd
from .utils import update_with_verbose, get_related_model
import django


FieldDoesNotExist = (
    django.db.models.fields.FieldDoesNotExist
    if django.VERSION < (1, 8)
    else django.core.exceptions.FieldDoesNotExist
)


def to_fields(qs, fieldnames):
    for fieldname in fieldnames:
        model = qs.model
        for fieldname_part in fieldname.split('__'):
            try:
                field = model._meta.get_field(fieldname_part)
            except FieldDoesNotExist:
                try:
                    rels = model._meta.get_all_related_objects_with_model()
                except AttributeError:
                    field = fieldname
                else:
                    for relobj, _ in rels:
                        if relobj.get_accessor_name() == fieldname_part:
                            field = relobj.field
                            model = field.model
                            break
            else:
                model = get_related_model(field)
        yield field


def is_values_queryset(qs):
    if django.VERSION < (1, 9):  # pragma: no cover
        return isinstance(qs, django.db.models.query.ValuesQuerySet)
    else:
        return qs._iterable_class == django.db.models.query.ValuesIterable


def read_frame(qs, fieldnames=(), index_col=None, coerce_float=False,
               verbose=True, datetime_index=False, column_names=None):
    """
    Returns a dataframe from a QuerySet

    Optionally specify the field names/columns to utilize and
    a field as the index

    Parameters
    ----------

    qs: The Django QuerySet.
    fieldnames: The model field names to use in creating the frame.
         You can span a relationship in the usual Django way
         by using  double underscores to specify a related field
         in another model
         You can span a relationship in the usual Django way
         by using  double underscores to specify a related field
         in another model

    index_col: specify the field to use  for the index. If the index
               field is not in the field list it will be appended

    coerce_float : boolean, default False
        Attempt to convert values to non-string, non-numeric data (like
        decimal.Decimal) to floating point, useful for SQL result sets

    verbose:  boolean If  this is ``True`` then populate the DataFrame with the
                human readable versions of any foreign key fields else use
                the primary keys values.
                The human readable version of the foreign key field is
                defined in the ``__unicode__`` or ``__str__``
                methods of the related class definition

    datetime_index: specify whether index should be converted to a
                    DateTimeIndex.

    column_names: If not None, use to override the column names in the
                  DateFrame
    """

    if fieldnames:
        fieldnames = pd.unique(fieldnames)
        if index_col is not None and index_col not in fieldnames:
            # Add it to the field names if not already there
            fieldnames = tuple(fieldnames) + (index_col,)
            if column_names:
                column_names = tuple(column_names) + (index_col,)
        fields = to_fields(qs, fieldnames)
    elif is_values_queryset(qs):
        if django.VERSION < (1, 9):  # pragma: no cover
            annotation_field_names = list(qs.query.annotation_select)

            if annotation_field_names is None:
                annotation_field_names = []

            extra_field_names = qs.extra_names
            if extra_field_names is None:
                extra_field_names = []

            select_field_names = qs.field_names

        else:  # pragma: no cover
            annotation_field_names = list(qs.query.annotation_select)
            extra_field_names = list(qs.query.extra_select)
            select_field_names = list(qs.query.values_select)

        fieldnames = select_field_names + annotation_field_names + \
            extra_field_names
        fields = [None if '__' in f else qs.model._meta.get_field(f)
                  for f in select_field_names] + \
            [None] * (len(annotation_field_names) + len(extra_field_names))

        uniq_fields = set()
        fieldnames, fields = zip(
            *(f for f in zip(fieldnames, fields)
              if f[0] not in uniq_fields and not uniq_fields.add(f[0])))
    else:
        fields = qs.model._meta.fields
        fieldnames = [f.name for f in fields]
        fieldnames += list(qs.query.annotation_select.keys())

    if is_values_queryset(qs):
        recs = list(qs)
    else:
        recs = list(qs.values_list(*fieldnames))

    df = pd.DataFrame.from_records(
        recs,
        columns=column_names if column_names else fieldnames,
        coerce_float=coerce_float
    )

    if verbose:
        update_with_verbose(df, fieldnames, fields)

    if index_col is not None:
        df.set_index(index_col, inplace=True)

    if datetime_index:
        df.index = pd.to_datetime(df.index, errors="ignore")
    return df
