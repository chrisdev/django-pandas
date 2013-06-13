from django.test import TestCase
import pandas as pd
import numpy as np
from .models import DataFrame, FlatTimeSeries
import pandas.util.testing as tm


class ManagerTest(TestCase):

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
        self.ts = tm.makeTimeDataFrame()
        self.ts.columns = ['col1', 'col2', 'col3', 'col4']
        create_list = []
        for ix, cols in self.ts.iterrows():
            create_list.append(FlatTimeSeries(date_ix=ix, col1=cols['col1'],
                                              col2=cols['col2'],
                                              col3=cols['col3'],
                                              col4=cols['col4'])
                               )
        FlatTimeSeries.objects.bulk_create(create_list)

    def test_basic(self):
        qs = DataFrame.objects.all()
        df = qs.to_dataframe()
        n, c = df.shape
        self.assertEqual(n, qs.count())
        flds = DataFrame._meta.get_all_field_names()
        self.assertEqual(c, len(flds))
        qs2 = DataFrame.objects.filter(index__in=['a', 'b', 'c'])
        df2 = qs2.to_dataframe('col1', 'col2', 'col3', index_field='index')
        n, c = df2.shape
        self.assertEqual((n, c), (3, 3))
        #import ipdb; ipdb.set_trace()

    def test_fields(self):
        pass
        #import ipdb; ipdb.set_trace()
