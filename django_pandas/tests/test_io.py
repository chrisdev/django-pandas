from django.test import TestCase
import pandas as pd
import numpy as np
from .models import MyModel
from django_pandas.io import read_frame


class IOTest(TestCase):

    def setUp(self):
        data = {
            'col1': np.array([1, 2, 3, 5, 6, 5, 5]),
            'col2': np.array([10.0, 2.4, 3.0, 5, 6, np.nan, 5]),
            'col3': np.array([9.5, 2.4, 3.0, 5, 6, 7.5, 2.5]),
            'col4':  np.array([9, 2, 3, 5, 6, 7, 2]),
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
        flds = MyModel._meta.get_all_field_names()
        self.assertEqual(c, len(flds))
        df1 = read_frame(qs, 'col1', 'col2')
        self.assertEqual(df1.shape, (qs.count(), 2))

    def test_index(self):
        qs = MyModel.objects.all()
        df = read_frame(qs, 'col1', 'col2', 'col3', 'col4',
                        index_col='index_col')
        self.assertEqual(df.shape, (qs.count(), 4))
        self.assertEqual(set(df.index.tolist()),
                         set(qs.values_list('index_col', flat=True)))
