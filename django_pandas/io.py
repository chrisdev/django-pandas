import pandas as pd
from .utils import update_with_verbose


def check_can_do_verbose(fieldnames):
    for fieldname in fieldnames:
        if '__' in fieldname:
            return False
    return True


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
        verbose = check_can_do_verbose(fieldnames)

        if index_col is not None and index_col not in fieldnames:
            # Add it to the field names if not already there
            fieldnames = tuple(fieldnames) + (index_col,)

        if verbose:
            get_field = qs.model._meta.get_field

            fields = [get_field(fieldname) for fieldname in fieldnames]
    else:
        fields = qs.model._meta.fields
        fieldnames = [f.name for f in fields]

    recs = list(qs.values_list(*fieldnames))

    if verbose:
        update_with_verbose(recs, fields)

    df = pd.DataFrame.from_records(recs, columns=fieldnames,
                                   coerce_float=coerce_float)
    if index_col is not None:
        df = df.set_index(index_col)

    return df
