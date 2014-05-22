from django.db.models.query import QuerySet, ValuesListQuerySet, ValuesQuerySet
from model_utils.managers import PassThroughManager
from .io import read_frame


class DataFrameMixin(object):

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
                 human readable versions for foreign key fields else
                 the primary keys values will be used for foreign key fields.
                 The human readable version of the foreign key field is
                 defined in the ``__unicode__`` or ``__str__``
                 methods of the related class definition
        """
        df = self.to_dataframe(fieldnames, verbose=verbose)

        return df.pivot_table(values=values, fill_value=fill_value, rows=rows,
                              cols=cols, aggfunc=aggfunc, margins=margins,
                              dropna=dropna)

    def to_timeseries(self, fieldnames=(), verbose=True,
                      index=None, storage='wide',
                      values=None, pivot_columns=None, freq=None,
                      rs_kwargs=None):
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


        pivot_column:  Required once the you specify `long` format
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
                  the primary keys values.
                  The human readable version of the foreign key field is
                  defined in the ``__unicode__`` or ``__str__``
                  methods of the related class definition
        """
        if index is None:
            raise AssertionError('You must supply an index field')
        if storage not in ('wide', 'long'):
            raise AssertionError('storage must be wide or long')
        if rs_kwargs is None:
            rs_kwargs = {}

        if storage == 'wide':
            df = self.to_dataframe(fieldnames, verbose=verbose, index=index)
        else:
            df = self.to_dataframe(fieldnames, verbose=verbose)
            if values is None:
                raise AssertionError('You must specify a values field')

            if pivot_columns is None:
                raise AssertionError('You must specify pivot_columns')

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
                 the primary keys values will be used for foreign key fields.
                 The human readable version of the foreign key field is
                 defined in the ``__unicode__`` or ``__str__``
                 methods of the related class definition

        """

        df = read_frame(self, fieldnames=fieldnames, verbose=verbose,
                        index_col=index,
                        coerce_float=coerce_float)

        return df


class ValuesMixin(object):
    """
    Mixin for overriding return type for values() and values_list().
    """

    def values(self, *fields):
        return self._clone(klass=DataFrameValuesQuerySet, setup=True, _fields=fields)

    def values_list(self, *fields, **kwargs):
        flat = kwargs.pop('flat', False)
        if kwargs:
            raise TypeError('Unexpected keyword arguments to values_list: %s'
                    % (list(kwargs),))
        if flat and len(fields) > 1:
            raise TypeError("'flat' is not valid when values_list is called with more than one field.")
        return self._clone(klass=DataFrameValuesListQuerySet, setup=True, flat=flat,
                _fields=fields)


class ConstraintValuesMixin(object):
    """
    Limits field list for values() and values_list() with original
    field list.
    """

    def values(self, *fields):
        fields = filter(lambda f: f in self._fields, fields)
        return super(ConstraintValuesMixin, self).values(*fields)

    def values_list(self, *fields, **kwargs):
        fields = filter(lambda f: f in self._fields, fields)
        return super(ConstraintValuesMixin, self).values_list(*fields, **kwargs)


class DataFrameValuesQuerySet(DataFrameMixin, ConstraintValuesMixin,
                              ValuesMixin, ValuesQuerySet):
    pass


class DataFrameValuesListQuerySet(DataFrameMixin, ConstraintValuesMixin,
                                  ValuesMixin, ValuesListQuerySet):
    pass


class DataFrameQuerySet(DataFrameMixin, ValuesMixin, QuerySet):
    pass


class DataFrameManager(PassThroughManager):

    def get_query_set(self):
        return DataFrameQuerySet(self.model)
