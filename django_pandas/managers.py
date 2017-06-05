from django.db.models.query import QuerySet
from .io import read_frame
import django
from django.db import models


class PassThroughManagerMixin(object):
    """
    A mixin that enables you to call custom QuerySet methods from your manager.
    """
    _deny_methods = ['__getstate__', '__setstate__', '__getinitargs__',
                     '__getnewargs__', '__copy__', '__deepcopy__', '_db',
                     '__slots__']

    def __init__(self, queryset_cls=None):
        self._queryset_cls = queryset_cls
        super(PassThroughManagerMixin, self).__init__()

    def __getattr__(self, name):
        if name in self._deny_methods:
            raise AttributeError(name)
        if django.VERSION < (1, 6, 0):
            return getattr(self.get_query_set(), name)
        return getattr(self.get_queryset(), name)

    def __dir__(self):
        my_values = frozenset(dir(type(self)))
        my_values |= frozenset(dir(self.get_query_set()))
        return list(my_values)

    def get_queryset(self):
        try:
            qs = super(PassThroughManagerMixin, self).get_queryset()
        except AttributeError:
            qs = super(PassThroughManagerMixin, self).get_query_set()
        if self._queryset_cls is not None:
            qs = qs._clone(klass=self._queryset_cls)
        return qs

    get_query_set = get_queryset

    @classmethod
    def for_queryset_class(cls, queryset_cls):
        return create_pass_through_manager_for_queryset_class(
            cls, queryset_cls)


class PassThroughManager(PassThroughManagerMixin, models.Manager):
    """
    Inherit from this Manager to enable you to call any methods from your
    custom QuerySet class from your manager. Simply define your QuerySet
    class, and return an instance of it from your manager's `get_queryset`
    method.

    Alternately, if you don't need any extra methods on your manager that
    aren't on your QuerySet, then just pass your QuerySet class to the
    ``for_queryset_class`` class method.

    class PostQuerySet(QuerySet):
        def enabled(self):
            return self.filter(disabled=False)

    class Post(models.Model):
        objects = PassThroughManager.for_queryset_class(PostQuerySet)()

    """
    pass


def create_pass_through_manager_for_queryset_class(base, queryset_cls):
    class _PassThroughManager(base):
        def __init__(self, *args, **kwargs):
            return super(_PassThroughManager, self).__init__(*args, **kwargs)

        def get_queryset(self):
            qs = super(_PassThroughManager, self).get_queryset()
            return qs._clone(klass=queryset_cls)

        get_query_set = get_queryset

    return _PassThroughManager


class DataFrameQuerySet(QuerySet):

    def to_pivot_table(self, fieldnames=(), verbose=True,
                       values=None, rows=None, cols=None,
                       aggfunc='mean', fill_value=None, margins=False,
                       dropna=True):
        """
        A convenience method for creating a spread sheet style pivot table
        as a DataFrame
        Parameters
        ----------
        fieldnames:  The model field names(columns) to utilise in creating
                     the DataFrame. You can span a relationships in the usual
                     Django ORM way by using the foreign key field name
                     separated by double underscores and refer to a field
                     in a related model.

        values:  The field to use to calculate the values to aggregate.

        rows:  The list of field names to group on
               Keys to group on the x-axis of the pivot table

        cols:  The list of column names or arrays to group on
               Keys to group on the y-axis of the pivot table

        aggfunc:  How to arregate the values. By default this would be
                  ``numpy.mean``. A list of aggregates functions can be passed
                  In this case the resulting pivot table will have
                  hierarchical columns whose top level are the function names
                 (inferred from the function objects themselves)

        fill_value:  A scalar value to replace the missing values with

        margins:  Boolean, default False Add all row / columns
                  (e.g. for subtotal / grand totals)

        dropna:  Boolean, default True.
                 Do not include columns whose entries are all NaN

        verbose: If  this is ``True`` then populate the DataFrame with the
                 human readable versions for foreign key fields else use the
                 actual values set in the model
        """
        df = self.to_dataframe(fieldnames, verbose=verbose)

        return df.pivot_table(values=values, fill_value=fill_value, index=rows,
                              columns=cols, aggfunc=aggfunc, margins=margins,
                              dropna=dropna)

    def to_timeseries(self, fieldnames=(), verbose=True,
                      index=None, storage='wide',
                      values=None, pivot_columns=None, freq=None,
                      coerce_float=False, rs_kwargs=None):
        """
        A convenience method for creating a time series DataFrame i.e the
        DataFrame index will be an instance of  DateTime or PeriodIndex

        Parameters
        ----------

        fieldnames:  The model field names(columns) to utilise in creating
                     the DataFrame. You can span a relationships in the usual
                     Django ORM way by using the foreign key field name
                     separated by double underscores and refer to a field
                     in a related model.

        index:  specify the field to use  for the index. If the index
                field is not in fieldnames it will be appended. This
                is mandatory for timeseries.

        storage:  Specify if the queryset uses the
                  ``wide`` format

                  date       |  col1| col2| col3|
                  -----------|------|-----|-----|
                  2001-01-01-| 100.5| 23.3|  2.2|
                  2001-02-01-| 106.3| 17.0|  4.6|
                  2001-03-01-| 111.7| 11.1|  0.7|

                  or the `long` format.

                  date       |values| names|
                  -----------|------|------|
                  2001-01-01-| 100.5|  col1|
                  2001-02-01-| 106.3|  col1|
                  2001-03-01-| 111.7|  col1|
                  2001-01-01-|  23.3|  col2|
                  2001-02-01-|  17.0|  col2|
                  2001-01-01-|  23.3|  col2|
                  2001-02-01-|   2.2|  col3|
                  2001-03-01-|   4.6|  col3|
                  2001-03-01-|   0.7|  col3|


        pivot_columns:  Required once the you specify `long` format
                       storage. This could either be a list or string
                       identifying the field name or combination of field.
                       If the pivot_column is a single column then the
                       unique values in this column become a new columns in
                       the DataFrame If the pivot column is a list the values
                       in these columns are concatenated (using the '-'
                       as a separator) and these values are used for the new
                       timeseries columns

        values:  Also required if you utilize the `long` storage the
                 values column name is use for populating new frame values

        freq:  The offset string or object representing a target conversion

        rs_kwargs:  A dictonary of keyword arguments based on the
                    ``pandas.DataFrame.resample`` method

        verbose:  If  this is ``True`` then populate the DataFrame with the
                  human readable versions of any foreign key fields else use
                  the primary keys values else use the actual values set
                  in the model.
                  
        coerce_float:   Attempt to convert values to non-string, non-numeric
                        objects (like decimal.Decimal) to floating point.
        """
        assert index is not None, 'You must supply an index field'
        assert storage in ('wide', 'long'), 'storage must be wide or long'
        if rs_kwargs is None:
            rs_kwargs = {}

        if storage == 'wide':
            df = self.to_dataframe(fieldnames, verbose=verbose, index=index,
                                   coerce_float=True)
        else:
            df = self.to_dataframe(fieldnames, verbose=verbose,
                                   coerce_float=True)
            assert values is not None, 'You must specify a values field'
            assert pivot_columns is not None, 'You must specify pivot_columns'

            if isinstance(pivot_columns, (tuple, list)):
                df['combined_keys'] = ''
                for c in pivot_columns:
                    df['combined_keys'] += df[c].str.upper() + '.'

                df['combined_keys'] += values.lower()

                df = df.pivot(index=index,
                              columns='combined_keys',
                              values=values)
            else:
                df = df.pivot(index=index,
                              columns=pivot_columns,
                              values=values)

        if freq is not None:
            df = df.resample(freq, **rs_kwargs)

        return df

    def to_dataframe(self, fieldnames=(), verbose=True, index=None,
                     coerce_float=False):
        """
        Returns a DataFrame from the queryset

        Paramaters
        -----------

        fieldnames:  The model field names(columns) to utilise in creating
                     the DataFrame. You can span a relationships in the usual
                     Django ORM way by using the foreign key field name
                     separated by double underscores and refer to a field
                     in a related model.


        index:  specify the field to use  for the index. If the index
                field is not in fieldnames it will be appended. This
                is mandatory for timeseries.

        verbose: If  this is ``True`` then populate the DataFrame with the
                 human readable versions for foreign key fields else
                 use the actual values set in the model
        
        coerce_float:   Attempt to convert values to non-string, non-numeric 
                        objects (like decimal.Decimal) to floating point.
        """

        return read_frame(self, fieldnames=fieldnames, verbose=verbose,
                          index_col=index, coerce_float=coerce_float)


if django.VERSION < (1, 7):
    class DataFrameManager(PassThroughManager):
        def get_query_set(self):
            return DataFrameQuerySet(self.model)

else:
    DataFrameManager = models.Manager.from_queryset(DataFrameQuerySet)
