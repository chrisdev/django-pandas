from django.test import TestCase
import pandas as pd
import numpy as np
import pickle
import django
from .models import (
    DataFrame, WideTimeSeries,
    LongTimeSeries, PivotData, MyModelChoice, Dude, Car, Spot
)
import pandas.util.testing as tm


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
        if django.VERSION < (1, 10):
            flds = DataFrame._meta.get_all_field_names()
        else:
            flds = [f.name for f in DataFrame._meta.get_fields()]
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

    def setUp(self):
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

        create_list = [LongTimeSeries(date_ix=r[0], series_name=r[1][0],
                                      value=r[1][1])
                       for r in self.ts2.iterrows()]

        LongTimeSeries.objects.bulk_create(create_list)

    def test_widestorage(self):

        qs = WideTimeSeries.objects.all()

        df = qs.to_timeseries(index='date_ix', storage='wide')

        self.assertEqual(df.shape, (qs.count(), 5))
        self.assertIsInstance(df.index, pd.tseries.index.DatetimeIndex)
        self.assertIsNone(df.index.freq)

    def test_longstorage(self):
        qs = LongTimeSeries.objects.all()
        df = qs.to_timeseries(index='date_ix', pivot_columns='series_name',
                              values='value',
                              storage='long')
        self.assertEqual(set(qs.values_list('series_name', flat=True)),
                         set(df.columns.tolist()))

        self.assertEqual(qs.filter(series_name='A').count(), len(df['A']))
        self.assertIsInstance(df.index, pd.tseries.index.DatetimeIndex)
        self.assertIsNone(df.index.freq)

    def test_resampling(self):
        qs = LongTimeSeries.objects.all()
        rs_kwargs = {'how': 'sum', 'kind': 'period'}
        df = qs.to_timeseries(index='date_ix', pivot_columns='series_name',
                              values='value', storage='long',
                              freq='M', rs_kwargs=rs_kwargs)

        self.assertEqual([d.month for d in qs.dates('date_ix', 'month')],
                         df.index.month.tolist())

        self.assertIsInstance(df.index, pd.tseries.period.PeriodIndex)
        #try on a  wide time seriesd

        qs2 = WideTimeSeries.objects.all()

        df1 = qs2.to_timeseries(index='date_ix', storage='wide',
                                freq='M', rs_kwargs=rs_kwargs)

        self.assertEqual([d.month for d in qs.dates('date_ix', 'month')],
                         df1.index.month.tolist())

        self.assertIsInstance(df1.index, pd.tseries.period.PeriodIndex)

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
            'values' : 'value',
            'storage' : 'long'}
        kwargs.pop('values')
        self.assertRaises(AssertionError, qs.to_timeseries, **kwargs)
        kwargs['values'] = 'value'
        kwargs.pop('pivot_columns')
        self.assertRaises(AssertionError, qs.to_timeseries, **kwargs)
        ##df = qs.to_timeseries(index='date_ix', pivot_columns='series_name',
                                ##values='value',
                                ##storage='long')


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

        create_list = [PivotData(row_col_a=r[1][0], row_col_b=r[1][1],
                                 row_col_c=r[1][2], value_col_d=r[1][3],
                                 value_col_e=r[1][4], value_col_f=r[1][5])
                       for r in self.data.iterrows()]

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
            Dude.objects.create(name='His Dudeness', abides=False, has_rug=True)
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
                # manager only method shouldn't appear on the non AbidingManager
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
                name='The Crux', owner=self.other_dude, closed=True, secure=True,
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
                name='The Secret Crib', owner=self.dude, closed=False, secure=True,
                secret=True)
            self.assertEqual(self.dude.spots_owned.count(), 1)

        def test_related_manager_create(self):
            self.dude.spots_owned.create(name='The Crib', closed=True, secure=True)
