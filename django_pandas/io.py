import pandas as pd
from django.db import connections
from pandas.io.sql import read_frame
from .utils import update_with_verbose


def to_fields(qs, fieldnames):
    fields = []
    for fieldname in fieldnames:
        model = qs.model
        for fieldname_part in fieldname.split('__'):
            field = model._meta.get_field(fieldname_part)
            if field.get_internal_type() == 'ForeignKey':
                model = field.rel.to
        fields.append(field)
    return fields


def read_frame(qs, fieldnames=(), index_col=None, coerce_float=False,
               verbose=True):
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
   """
    if fieldnames:
        if index_col is not None and index_col not in fieldnames:
            # Add it to the field names if not already there
            fieldnames = tuple(fieldnames) + (index_col,)

        fields = to_fields(qs, fieldnames)
    else:
        fields = qs.model._meta.fields
        fieldnames = [f.name for f in fields]

    compiler = qs.query.get_compiler(using=qs.db)
    connection = connections[qs.db]
    sql, args = compiler.as_sql()
    df = read_frame(sql, connection, coerce_float=coerce_float, params=args)
    df.columns = qs.field_names

    if verbose:
        update_with_verbose(df, fieldnames, fields)

    if index_col is not None:
        df.set_index(index_col, inplace=True)

    return df
