from django.db.models.query import QuerySet
import numpy as np
from pandas import DataFrame
from model_utils.managers import PassThroughManager


class DataFrameQuerySet(QuerySet):
    def to_dataframe(self, *fields, **kwargs):
        coerce_float = kwargs.pop('coerce_float', True)
        index_field = kwargs.pop('index_field', None)
        freq = kwargs.pop('freq', None)
        fill_method = kwargs.pop('fill_method', None)
        if index_field is not None:
            # add it to the fields if not already there
            if index_field not in fields:
                fields = fields + (index_field,)

        qs = self.values_list(*fields)
        recs = np.core.records.fromrecords(qs, names=qs.field_names)

        df = DataFrame.from_records(recs, coerce_float=coerce_float)
        if index_field is not None:

            df = df.set_index(index_field)

        if freq is not None:
            df.index = df.index.normalize()
            if fill_method is not None:
                df = df.asfreq(freq, method=fill_method)
            else:
                df = df.asfreq(freq)

        return df


class DataFrameManager(PassThroughManager):
    def get_query_set(self):
        return DataFrameQuerySet(self.model)
