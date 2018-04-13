import sys
from unittest import expectedFailure

from django.test import TestCase
import django
from django.db.models import Sum
import pandas as pd
import numpy as np
from .models import MyModel, Trader, Security, TradeLog, TradeLogNote, MyModelChoice, Portfolio
from django_pandas.tests import models
from django_pandas.io import read_frame


class IOTest(TestCase):

    def setUp(self):
        data = {
            'col1': np.array([1, 2, 3, 5, 6, 5, 5]),
            'col2': np.array([10.0, 2.4, 3.0, 5, 6, np.nan, 5]),
            'col3': np.array([9.5, 2.4, 3.0, 5, 6, 7.5, 2.5]),
            'col4': np.array([9, 2, 3, 5, 6, 7, 2]),
        }
        index = pd.Index(['a', 'b', 'c', 'd', 'e', 'f', 'h'])

        self.df = pd.DataFrame(index=index, data=data)

        for ix, cols in self.df.iterrows():
            MyModel.objects.create(
                index_col=ix,
                col1=cols['col1'],
                col2=cols['col2'],
                col3=cols['col3'],
                col4=cols['col4']
            )

    def test_basic(self):
        qs = MyModel.objects.all()
        df = read_frame(qs)
        n, c = df.shape
        self.assertEqual(n, qs.count())
        from itertools import chain
        if django.VERSION < (1,10):
            fields = MyModel._meta.get_all_field_names()
        else:
            fields = list(set(chain.from_iterable((field.name, field.attname) if hasattr(field,'attname') else (field.name,)
                for field in MyModel._meta.get_fields()
                if not (field.many_to_one and field.related_model is None)
            )))
        self.assertEqual(c, len(fields))
        df1 = read_frame(qs, ['col1', 'col2'])
        self.assertEqual(df1.shape, (qs.count(), 2))

    def assert_compress_basic(self, qs):
        df = read_frame(qs, compress=True)

        # Test automatic inference of dtypes
        self.assertEqual(df.col1.dtype, np.dtype('int32'))
        self.assertEqual(df.col2.dtype, np.dtype('float_'))
        self.assertEqual(df.col3.dtype, np.dtype('float_'))
        self.assertEqual(df.col4.dtype, np.dtype('int16'))

        # Compress should use less memory
        self.assertLess(df.memory_usage(deep=True).sum(), read_frame(qs).memory_usage(deep=True).sum())
        # Uses qs.iterator() rather than for x in qs.
        self.assertFalse(qs._result_cache)

    def test_compress_basic(self):
        qs = MyModel.objects.all()
        self.assert_compress_basic(qs)
        self.assert_compress_basic(qs.values())
        self.assert_compress_basic(qs.values_list())

    def test_compress_bad_argument(self):
        qs = MyModel.objects.all()
        bads = [(models.ByteField, np.int8), range(3), type, object(), 'a', 1.,
            {'IntegerField': int}, {int: models.ByteField},
            {models.ByteField: 'asdf'}]
        for bad in bads:
            self.assertRaises(TypeError, read_frame, qs, compress=bad)

        self.assertRaises(
            ValueError, read_frame, qs, compress=True, coerce_float=True)

    def assert_default_compressable(self, df):
        for field in models.CompressableModel._meta.get_fields():
            if field.name == 'id':
                self.assertEqual(df['id'][0], 1)
                self.assertIs(df['id'].dtype, np.dtype('int32'))
            elif field.name == 'date':
                self.assertEqual(df['date'][0].to_pydatetime().date(), field.default)
            elif field.name == 'datetime':
                self.assertEqual(df['datetime'][0].to_pydatetime(), field.default)
            elif field.name == 'duration':
                self.assertEqual(df['duration'][0].to_pytimedelta(), field.default)
            elif field.name == 'nullboolean':
                self.assertEqual(df['nullboolean'].dtype, np.object_)
                self.assertIsNone(df['nullboolean'][0])
            elif isinstance(field.default, (str, bytes)):
                self.assertEqual(df[field.name].dtype, np.dtype(object))
            else:
                msg = 'Expected {} to have value {!r}, but was {!r}'.format(
                    field.name, field.default, df[field.name][0])
                self.assertEqual(df[field.name][0], field.default, msg)

    def test_compress_custom_field(self):
        models.CompressableModel().save()
        qs = models.CompressableModel.objects.all()

        # Specify a custom dtype for the custom field
        df1 = read_frame(qs, compress={models.ByteField: np.int8})
        self.assert_default_compressable(df1)
        self.assertEqual(df1.byte.dtype, np.int8)

        # Rely on finding the minimum specified parent class
        df2 = read_frame(qs, compress=True)
        self.assert_default_compressable(df2)
        self.assertEqual(df2.uint.dtype, np.uint32)
        self.assertEqual(df2.byte.dtype, np.int16)

        # Memory usage is ordered as df1 < df2 < read_frame(qs, compress=False)
        self.assertLess(df2.memory_usage(deep=True).sum(), read_frame(qs).memory_usage(deep=True).sum())
        self.assertLess(df1.memory_usage(deep=True).sum(), df2.memory_usage(deep=True).sum())
        # Uses qs.iterator() rather than for x in qs.
        self.assertFalse(qs._result_cache)

    def test_compress_nulls(self):
        maxs = dict(bigint=np.iinfo(np.int64).max, floating=sys.float_info.max,
            integer=np.iinfo(np.int32).max, nullboolean=True,
            uint=np.iinfo(np.uint32).max, ushort=np.iinfo(np.uint16).max,
            short=np.iinfo(np.int16).max, byte=np.iinfo(np.int8).max)
        mins = dict(bigint=np.iinfo(np.int64).min, floating=sys.float_info.min,
            integer=np.iinfo(np.int32).min, nullboolean=True,
            uint=np.iinfo(np.uint32).min, ushort=np.iinfo(np.uint16).min,
            short=np.iinfo(np.int16).min, byte=np.iinfo(np.int8).min)
        dbmaxs = models.CompressableModelWithNulls(**maxs)
        dbmaxs.save()
        dbnulls = models.CompressableModelWithNulls()
        dbnulls.save()
        dbmins = models.CompressableModelWithNulls(**mins)
        dbmins.save()
        qs = models.CompressableModelWithNulls.objects.all()
        df1 = read_frame(qs, compress={models.ByteField: np.int8})

        self.assertEqual(df1.bigint.dtype,   np.object_)
        self.assertEqual(df1.floating.dtype, np.float_)
        self.assertEqual(df1.integer.dtype,  np.float64)
        self.assertEqual(df1.nullboolean.dtype, np.object_)
        self.assertEqual(df1.uint.dtype,     np.float64)
        self.assertEqual(df1.ushort.dtype,   np.float32)
        self.assertEqual(df1.short.dtype,    np.float32)
        self.assertEqual(df1.byte.dtype,     np.float16)

        for col in df1.columns:
            if col == 'id':
                continue
            self.assertEqual(df1[col][0], maxs[col])
            self.assertTrue(df1[col][1] is None or np.isnan(df1[col][1]))
            self.assertEqual(df1[col][2], mins[col])

    def test_values(self):
        qs = MyModel.objects.all()
        qs = qs.extra(select={"ecol1": "col1+1"})
        qs = qs.values("index_col", "ecol1", "col1")
        qs = qs.annotate(scol1=Sum("col1"))
        df = read_frame(qs)
        self.assertEqual(list(df.columns),
                         ['index_col', 'col1', 'scol1', 'ecol1'])
        self.assertEqual(list(df["col1"]), list(df["scol1"]))

    def test_duplicate_annotation(self):
        qs = MyModel.objects.all()
        qs = qs.values('index_col')
        qs = qs.annotate(col1=Sum('col1'))
        qs = qs.values()
        df = read_frame(qs)
        self.assertEqual(list(df.columns),
                         ['id', 'index_col', 'col1', 'col2', 'col3', 'col4'])

    def test_choices(self):

        MyModelChoice.objects.create(col1=1, col2=9999.99)
        MyModelChoice.objects.create(col1=2, col2=0.99)
        MyModelChoice.objects.create(col1=3, col2=45.6)
        MyModelChoice.objects.create(col1=2, col2=2.6)

        qs = MyModelChoice.objects.all()
        df = read_frame(qs, verbose=True)
        self.assertEqual(df.col1[0], 'First')
        self.assertEqual(df.col1[1], 'Second')
        self.assertEqual(df.col1[2], 'Third')
        self.assertEqual(df.col1[3], 'Second')
        df = read_frame(qs, verbose=False)
        self.assertEqual(df.col1[0], 1)
        self.assertEqual(df.col1[1], 2)
        self.assertEqual(df.col1[2], 3)
        self.assertEqual(df.col1[3], 2)

    def test_index(self):
        qs = MyModel.objects.all()
        df = read_frame(qs, ['col1', 'col2', 'col3', 'col4'],
                        index_col='index_col')
        self.assertEqual(df.shape, (qs.count(), 4))
        self.assertEqual(set(df.index.tolist()),
                         set(qs.values_list('index_col', flat=True)))


class RelatedFieldsTest(TestCase):
    def setUp(self):
        bob = Trader.objects.create(name="Jim Brown")
        fish = Trader.objects.create(name="Fred Fish")
        abc = Security.objects.create(symbol='ABC', isin='999901')
        zyz = Security.objects.create(symbol='ZYZ', isin='999907')
        TradeLog.objects.create(trader=bob, symbol=None,
                                log_datetime='2013-01-01T09:30:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aaa'))
        TradeLog.objects.create(trader=bob, symbol=None,
                                log_datetime='2013-01-01T10:00:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aab'))
        TradeLog.objects.create(trader=bob, symbol=abc,
                                log_datetime='2013-01-01T10:30:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aac'))
        TradeLog.objects.create(trader=bob, symbol=abc,
                                log_datetime='2013-01-01T11:00:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aad'))
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T09:30:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aae'))
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T10:00:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aaf'))
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T10:30:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aag'))
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T11:00:00',
                                price=30, volume=300,
                                note=TradeLogNote.objects.create(note='aah'))
        value = Portfolio.objects.create(name="Fund 1")
        value.securities.add(abc)
        value.securities.add(zyz)
        growth = Portfolio.objects.create(name="Fund 2")
        growth.securities.add(abc)

    def test_compress_fk(self):
        qs = TradeLog.objects.all()
        # trader and trader_id are both the foreign key id column on TradeLog.
        # trader__id is the id column on Trader via a JOIN.
        cols = ['trader', 'trader_id', 'trader__id']
        df = read_frame(qs, cols, verbose=False, compress=True)

        self.assertEqual(df.shape, (qs.count(), len(cols)))
        self.assertTrue(df.trader.equals(df.trader__id))
        self.assertTrue(df.trader_id.equals(df.trader__id))
        self.assertEqual(df.trader.dtype, np.dtype('int32'))
        self.assertEqual(df.trader_id.dtype, np.dtype('int32'))
        self.assertEqual(df.trader__id.dtype, np.dtype('int32'))
        self.assertCountEqual(
            df.trader_id, qs.values_list('trader_id', flat=True))

    def test_compress_fk_nullable(self):
        qs = TradeLog.objects.all()
        cols = ['symbol', 'symbol_id']
        df = read_frame(qs, cols, verbose=False, compress=True)

        self.assertEqual(df.shape, (qs.count(), len(cols)))
        self.assertTrue(df.symbol.equals(df.symbol_id))
        self.assertEqual(df.symbol.dtype, np.dtype(float))
        self.assertEqual(df.symbol_id.dtype, np.dtype(float))
        self.assertCountEqual(
            [None if pd.isna(x) else x for x in df.symbol],
            qs.values_list('symbol_id', flat=True))

    @expectedFailure
    def test_compress_fk_nullable_join(self):
        qs = TradeLog.objects.all()
        # symbol is the foreign key id column on TradeLog. symbol__id is the id
        # column on Security via a JOIN.
        cols = ['symbol', 'symbol__id']
        df = read_frame(qs, cols, verbose=False, compress=True)

        self.assertEqual(df.shape, (qs.count(), len(cols)))
        self.assertTrue(df.symbol.equals(df.symbol__id))
        self.assertEqual(df.symbol.dtype, np.dtype(float))
        self.assertEqual(df.symbol__id.dtype, np.dtype(float))
        self.assertCountEqual(
            [None if pd.isna(x) else x for x in df.symbol],
            qs.values_list('symbol__id', flat=True))

    def test_verbose(self):
        qs = TradeLog.objects.all()
        df = read_frame(qs, verbose=True)
        self.assertListEqual(
            list(qs.values_list('trader__name', flat=True)),
            df.trader.tolist()
        )
        df1 = read_frame(qs, verbose=False)
        self.assertListEqual(
            list(qs.values_list('trader__pk', flat=True)),
            df1.trader.tolist()
        )

        # Testing verbose with annotated column:
        if django.VERSION >= (1, 10):
            from django.db.models import F, FloatField
            from django.db.models.functions import Cast
            qs1 = TradeLog.objects.all().annotate(
                total_sum=Cast(F('price') * F('volume'), FloatField()),
            )
            df2 = read_frame(
                qs1, fieldnames=['trader', 'total_sum'])
            self.assertListEqual(
                list(qs1.values_list('total_sum', flat=True)),
                df2.total_sum.tolist()
            )
            self.assertListEqual(
                list(qs1.values_list('trader__name', flat=True)),
                df2.trader.tolist()
            )

    def test_verbose_duplicates_fieldnames(self):
        qs = TradeLog.objects.all()
        df = read_frame(qs, fieldnames=['trader', 'trader', 'price'])
        self.assertListEqual(
            list(qs.values_list('price', flat=True)),
            df.price.tolist()
        )

    def test_verbose_duplicate_values(self):
        qs = TradeLog.objects.all()
        qs = qs.values('trader', 'trader', 'price')
        df = read_frame(qs)
        self.assertListEqual(
            list(qs.values_list('price', flat=True)),
            df.price.tolist()
        )

    def test_related_selected_field(self):
        qs = TradeLog.objects.all().values('trader__name')
        df = read_frame(qs)
        self.assertEqual(list(df.columns), ['trader__name'])

    def test_related_cols(self):
        qs = TradeLog.objects.all()
        cols = ['log_datetime', 'symbol', 'symbol__isin', 'trader__name',
                'price', 'volume', 'note__note']
        df = read_frame(qs, cols, verbose=False)

        self.assertEqual(df.shape, (qs.count(), len(cols)))
        self.assertListEqual(
            list(qs.values_list('symbol__isin', flat=True)),
            df.symbol__isin.tolist()
        )
        self.assertListEqual(
            list(qs.values_list('trader__name', flat=True)),
            df.trader__name.tolist()
        )

    def test_many_to_many(self):
        qs = Portfolio.objects.all()
        cols = ['name', 'securities__symbol', 'securities__tradelog__log_datetime']
        df = read_frame(qs, cols, verbose=True)

        denormalized = Portfolio.objects.all().values_list(*cols)
        self.assertEqual(df.shape, (len(denormalized), len(cols)))
        for idx, row in enumerate(denormalized):
            self.assertListEqual(
                df.iloc[idx].tolist(),
                list(row)
            )
