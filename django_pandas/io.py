import pandas as pd


def read_frame(qs, *fields, **kwargs):
    """
    Returns a dataframe form a QuerySet

    Optionally specify the fields/columns to utilize and
    specify a fields as the index

    Parameters
    ----------

    qs: The Django QuerySet.
    fields: The model field names to use in creating the frame.
         You can span a relationship in the usual Django way
         by using  double underscores to specify a related field
         in another model
         You can span a relationship in the usual Django way
         by using  double underscores to specify a related field
         in another model

    index_col: specify the field to use  for the index. If the index
               field is not in the field list it will be appended

    coerce_float : boolean, default True
        Attempt to convert values to non-string, non-numeric objects (like
        decimal.Decimal) to floating point, useful for SQL result sets
   """

    index_col = kwargs.pop('index_col', None)
    coerce_float = kwargs.pop('coerce_float', False)
    if not fields:
        fields = tuple([f.name for f in qs.model._meta.fields])

    if index_col is not None:
        # add it to the fields if not already there
        if index_col not in fields:
            fields = fields + (index_col,)

    recs = list(qs.values_list(*fields))

    df = pd.DataFrame.from_records(recs, columns=fields,
                                   coerce_float=coerce_float)
    if index_col is not None:
        df = df.set_index(index_col)

    return df
