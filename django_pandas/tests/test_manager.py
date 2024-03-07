from datetime import datetime

from django.test import TestCase
import pandas as pd
import numpy as np
import pickle
import django
from pandas.core.indexes.datetimes import bdate_range

from .models import (
    DataFrame, WideTimeSeries, WideTimeSeriesDateField,
    LongTimeSeries, PivotData, Dude, Car, Spot
)
try:
    import pandas._testing as tm
except ImportError:
    import pandas.util.testing as tm

import semver

PANDAS_VERSIONINFO = semver.VersionInfo.parse(pd.__version__)

class DataFrameTest(TestCase):

    def setUp(self):
        data = {
            'col1': np.array([1, 2, 3, 5, 6, 5, 5]),
            'col2': np.array([10.0, 2.4, 3.0, 5, 6, 5, 5]),
            'col3': np.array([9.5, 2.4, 3.0, 5, 6, 7.5, 2.5]),
            'col4':  np.array([9, 2, 3, 5, 6, 7, 2]),
        }
        index = pd.Index(['a', 'b', 'c', 'd', 'e', 'f', 'h'])

        self.df = pd.DataFrame(index=index, data=data)

        for ix, cols in self.df.iterrows():
            DataFrame.objects.create(
                index=ix,
                col1=cols['col1'],
                col2=cols['col2'],
                col3=cols['col3'],
                col4=cols['col4']
            )

    def test_dataframe(self):
        qs = DataFrame.objects.all()
        df = qs.to_dataframe()

        n, c = df.shape
        self.assertEqual(n, qs.count())
        from itertools import chain
        if django.VERSION < (1, 10):
            flds = DataFrame._meta.get_all_field_names()
        else:
            flds = list(set(chain.from_iterable((field.name, field.attname)
                            if hasattr(field, 'attname') else (field.name,)
                            for field in DataFrame._meta.get_fields()
                            if not (field.many_to_one and
                                    field.related_model is None))))
        self.assertEqual(c, len(flds))
        qs2 = DataFrame.objects.filter(index__in=['a', 'b', 'c'])
        df2 = qs2.to_dataframe(['col1', 'col2', 'col3'], index='index')
        n, c = df2.shape
        self.assertEqual((n, c), (3, 3))


class TimeSeriesTest(TestCase):
    def unpivot(self, frame):
        N, K = frame.shape
        data = {'value': frame.values.ravel('F'),
                'variable': np.array(frame.columns).repeat(N),
                'date': np.tile(np.array(frame.index), K)}
        return pd.DataFrame(data, columns=['date', 'variable', 'value'])

    def _makeTimeDataFrame(self, n_rows: int) -> pd.DataFrame:
        # Beginning in 2.2 pandas._testing.makeTimeDataFrame was removed, however all that is required for the tests
        # in this module is a dataframe with columns A, B, C, D of random values indexed by a DatetimeIndex.
        data = {}
        for c in ['A', 'B', 'C', 'D']:
            dt = datetime(2000, 1, 1)
            dr = bdate_range(dt, periods=n_rows, freq='B', name=c)
            pd.DatetimeIndex(dr, name=c)

            data[c] = pd.Series(
                np.random.default_rng(2).standard_normal(n_rows),
                index=pd.DatetimeIndex(dr, name=c),
                name=c,
            )
        return pd.DataFrame(data)

    def setUp(self):
        if PANDAS_VERSIONINFO >= '2.2.0':
            self.ts = self._makeTimeDataFrame(100)
        else:
            self.ts = tm.makeTimeDataFrame(100)

        self.ts2 = self.unpivot(self.ts).set_index('date')
        self.ts.columns = ['col1', 'col2', 'col3', 'col4']
        create_list = []
        for ix, cols in self.ts.iterrows():
            create_list.append(WideTimeSeries(date_ix=ix, col1=cols['col1'],
                                              col2=cols['col2'],
                                              col3=cols['col3'],
                                              col4=cols['col4']))
        WideTimeSeries.objects.bulk_create(create_list)

        for ix, cols in self.ts.iterrows():
            create_list.append(WideTimeSeriesDateField(date_ix=ix, col1=cols['col1'],
                                                       col2=cols['col2'],
                                                       col3=cols['col3'],
                                                       col4=cols['col4']))
        WideTimeSeriesDateField.objects.bulk_create(create_list)

        create_list = [LongTimeSeries(date_ix=timestamp, series_name=s.iloc[0],
                                      value=s.iloc[1])
                       for timestamp, s in self.ts2.iterrows()]

        LongTimeSeries.objects.bulk_create(create_list)

    def test_widestorage(self):

        qs = WideTimeSeries.objects.all()

        df = qs.to_timeseries(index='date_ix', storage='wide')

        self.assertEqual(df.shape, (qs.count(), 5))
        self.assertIsInstance(df.index, pd.DatetimeIndex)
        self.assertIsNone(df.index.freq)

    def test_widestorage_datefield(self):

        qs = WideTimeSeriesDateField.objects.all()

        df = qs.to_timeseries(index='date_ix', storage='wide')

        self.assertIsInstance(df.index, pd.DatetimeIndex)

    def test_longstorage(self):
        qs = LongTimeSeries.objects.all()
        df = qs.to_timeseries(index='date_ix', pivot_columns='series_name',
                              values='value',
                              storage='long')
        self.assertEqual(set(qs.values_list('series_name', flat=True)),
                         set(df.columns.tolist()))

        self.assertEqual(qs.filter(series_name='A').count(), len(df['A']))
        self.assertIsInstance(df.index, pd.DatetimeIndex)
        self.assertIsNone(df.index.freq)

    def test_resampling(self):
        qs = LongTimeSeries.objects.all()
        agg_args = None
        agg_kwargs = None
        if PANDAS_VERSIONINFO >= '0.25.0':
            agg_kwargs = {'func': 'sum'}
        else:
            agg_args = ['sum']

        if PANDAS_VERSIONINFO >= '2.2.0':
            freq = 'ME'
        else:
            freq = 'M'

        df = qs.to_timeseries(index='date_ix', pivot_columns='series_name',
                              values='value', storage='long',
                              freq=freq,
                              agg_args=agg_args,
                              agg_kwargs=agg_kwargs)
        df.index = pd.PeriodIndex(df.index)

        self.assertEqual([d.month for d in qs.dates('date_ix', 'month')],
                         df.index.month.tolist())

        self.assertIsInstance(df.index, pd.PeriodIndex)
        #try on a  wide time seriesd

        qs2 = WideTimeSeries.objects.all()

        df1 = qs2.to_timeseries(index='date_ix', storage='wide',
                                freq=freq,
                                agg_args=agg_args,
                                agg_kwargs=agg_kwargs)
        df1.index = pd.PeriodIndex(df1.index)

        self.assertEqual([d.month for d in qs.dates('date_ix', 'month')],
                         df1.index.month.tolist())

        self.assertIsInstance(df1.index, pd.PeriodIndex)

    def test_bad_args_wide_ts(self):
        qs = WideTimeSeries.objects.all()
        rs_kwargs = {'how': 'sum', 'kind': 'period'}
        kwargs = {
            'fieldnames': ['col1', 'col2'],
            'freq': 'M', 'rs_kwargs': rs_kwargs
        }
        self.assertRaises(AssertionError, qs.to_timeseries, **kwargs)
        kwargs2 = {
            'index': 'date_ix',
            'fieldnames': ['col1', 'col2'],
            'storage': 'big',
            'freq': 'M', 'rs_kwargs': rs_kwargs
        }
        self.assertRaises(AssertionError, qs.to_timeseries, **kwargs2)

    def test_bad_args_long_ts(self):
        qs = LongTimeSeries.objects.all()
        kwargs = {
            'index': 'date_ix',
            'pivot_columns': 'series_name',
            'values': 'value',
            'storage': 'long'}
        kwargs.pop('values')
        self.assertRaises(AssertionError, qs.to_timeseries, **kwargs)
        kwargs['values'] = 'value'
        kwargs.pop('pivot_columns')
        self.assertRaises(AssertionError, qs.to_timeseries, **kwargs)
        # df = qs.to_timeseries(index='date_ix', pivot_columns='series_name',
        # values='value',
        # storage='long')

    def test_coerce_float(self):
        qs = LongTimeSeries.objects.all()
        ts = qs.to_timeseries(index='date_ix',
                              coerce_float=True).resample('D').sum()
        self.assertEqual(ts['value'].dtype, np.float64)

        # Testing on Wide Series

        qs = WideTimeSeries.objects.all()
        ts = qs.to_timeseries(index='date_ix',
                              coerce_float=True).resample('D').sum()
        self.assertEqual(ts['col1'].dtype, np.float64)
        self.assertEqual(ts['col2'].dtype, np.float64)
        self.assertEqual(ts['col3'].dtype, np.float64)
        self.assertEqual(ts['col4'].dtype, np.float64)


class PivotTableTest(TestCase):

    def setUp(self):
        self.data = pd.DataFrame({'row_col_a': ['foo', 'foo', 'foo', 'foo',
                                                'bar', 'bar', 'bar', 'bar',
                                                'foo', 'foo', 'foo'],
                                  'row_col_b': ['one', 'one', 'one', 'two',
                                                'one', 'one', 'one', 'two',
                                                'two', 'two', 'one'],
                                  'row_col_c': ['dull', 'dull',
                                                'shiny', 'dull',
                                                'dull', 'shiny',
                                                'shiny', 'dull',
                                                'shiny', 'shiny', 'shiny'],
                                  'value_col_d': np.random.randn(11),
                                  'value_col_e': np.random.randn(11),
                                  'value_col_f': np.random.randn(11)})
        create_list = [PivotData(row_col_a=r.iloc[0], row_col_b=r.iloc[1],
                                 row_col_c=r.iloc[2], value_col_d=r.iloc[3],
                                 value_col_e=r.iloc[4], value_col_f=r.iloc[5])
                       for _, r in self.data.iterrows()]

        PivotData.objects.bulk_create(create_list)

    def test_pivot(self):
        qs = PivotData.objects.all()
        rows = ['row_col_a', 'row_col_b']
        cols = ['row_col_c']

        pt = qs.to_pivot_table(values='value_col_d', rows=rows, cols=cols)
        self.assertEqual(pt.index.names, rows)
        self.assertEqual(pt.columns.names, cols)


if django.VERSION < (1, 9):

    class PassThroughManagerTests(TestCase):

        def setUp(self):
            Dude.objects.create(name='The Dude', abides=True, has_rug=False)
            Dude.objects.create(name='His Dudeness',
                                abides=False, has_rug=True)
            Dude.objects.create(name='Duder', abides=False, has_rug=False)
            Dude.objects.create(name='El Duderino', abides=True, has_rug=True)

        def test_chaining(self):
            self.assertEqual(Dude.objects.by_name('Duder').count(), 1)
            self.assertEqual(Dude.objects.all().by_name('Duder').count(), 1)
            self.assertEqual(Dude.abiders.rug_positive().count(), 1)
            self.assertEqual(Dude.abiders.all().rug_positive().count(), 1)

        def test_manager_only_methods(self):
            stats = Dude.abiders.get_stats()
            self.assertEqual(stats['rug_count'], 1)
            with self.assertRaises(AttributeError):
                Dude.abiders.all().get_stats()

        def test_queryset_pickling(self):
            qs = Dude.objects.all()
            saltyqs = pickle.dumps(qs)
            unqs = pickle.loads(saltyqs)
            self.assertEqual(unqs.by_name('The Dude').count(), 1)

        def test_queryset_not_available_on_related_manager(self):
            dude = Dude.objects.by_name('Duder').get()
            Car.objects.create(name='Ford', owner=dude)
            self.assertFalse(hasattr(dude.cars_owned, 'by_name'))

        def test_using_dir(self):
            # make sure introspecing via dir() doesn't actually cause queries,
            # just as a sanity check.
            with self.assertNumQueries(0):
                querysets_to_dir = (
                    Dude.objects,
                    Dude.objects.by_name('Duder'),
                    Dude.objects.all().by_name('Duder'),
                    Dude.abiders,
                    Dude.abiders.rug_positive(),
                    Dude.abiders.all().rug_positive()
                )
                for qs in querysets_to_dir:
                    self.assertTrue('by_name' in dir(qs))
                    self.assertTrue('abiding' in dir(qs))
                    self.assertTrue('rug_positive' in dir(qs))
                    self.assertTrue('rug_negative' in dir(qs))
                    # some standard qs methods
                    self.assertTrue('count' in dir(qs))
                    self.assertTrue('order_by' in dir(qs))
                    self.assertTrue('select_related' in dir(qs))
                    # make sure it's been de-duplicated
                    self.assertEqual(1, dir(qs).count('distinct'))

                # manager only method.
                self.assertTrue('get_stats' in dir(Dude.abiders))
                # manager only method shouldn't appear on the nonAbidingManager
                self.assertFalse('get_stats' in dir(Dude.objects))
                # standard manager methods
                self.assertTrue('get_query_set' in dir(Dude.abiders))
                self.assertTrue('contribute_to_class' in dir(Dude.abiders))

    class CreatePassThroughManagerTests(TestCase):

        def setUp(self):
            self.dude = Dude.objects.create(name='El Duderino')
            self.other_dude = Dude.objects.create(name='Das Dude')

        def test_reverse_manager(self):
            Spot.objects.create(
                name='The Crib', owner=self.dude, closed=True, secure=True,
                secret=False)
            self.assertEqual(self.dude.spots_owned.closed().count(), 1)
            Spot.objects.create(
                name='The Crux', owner=self.other_dude,
                closed=True, secure=True,
                secret=False
            )
            self.assertEqual(self.dude.spots_owned.closed().all().count(), 1)
            self.assertEqual(self.dude.spots_owned.closed().count(), 1)

        def test_related_queryset_pickling(self):
            Spot.objects.create(
                name='The Crib', owner=self.dude, closed=True, secure=True,
                secret=False)
            qs = self.dude.spots_owned.closed()
            pickled_qs = pickle.dumps(qs)
            unpickled_qs = pickle.loads(pickled_qs)
            self.assertEqual(unpickled_qs.secured().count(), 1)

        def test_related_queryset_superclass_method(self):
            Spot.objects.create(
                name='The Crib', owner=self.dude, closed=True, secure=True,
                secret=False)
            Spot.objects.create(
                name='The Secret Crib', owner=self.dude,
                closed=False, secure=True,
                secret=True)
            self.assertEqual(self.dude.spots_owned.count(), 1)

        def test_related_manager_create(self):
            self.dude.spots_owned.create(name='The Crib',
                                         closed=True, secure=True)
