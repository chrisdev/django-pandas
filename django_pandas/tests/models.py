from django.db import models
from django_pandas.managers import DataFrameManager


class DataFrame(models.Model):

    index = models.CharField(max_length=1)
    col1 = models.IntegerField()
    col2 = models.FloatField()
    col3 = models.FloatField()
    col4 = models.IntegerField()

    objects = DataFrameManager()

    def __unicode__(self):
        return "{} {} {} {}".format(
            self.index,
            self.col1,
            self.col2,
            self.col3,
            self.col4
        )


class LongTimeSeries(models.Model):
    date_ix = models.DateTimeField()
    series_name = models.CharField(max_length=100)
    value = models.FloatField()

    objects = DataFrameManager()

    def __unicode__(self):
        return "{} {} {}".format(self.date_ix,
                                 self.series_name,
                                 self.value)


class WideTimeSeries(models.Model):
    date_ix = models.DateTimeField()
    col1 = models.FloatField()
    col2 = models.FloatField()
    col3 = models.FloatField()
    col4 = models.FloatField()

    objects = DataFrameManager()

    def __unicode__(self):
        return "{} {} {} {}".format(
            self.date_ix,
            self.col1,
            self.col2,
            self.col3,
            self.col4
        )


class PivotData(models.Model):
    row_col_a = models.CharField(max_length=15)
    row_col_b = models.CharField(max_length=15)
    row_col_c = models.CharField(max_length=15)
    value_col_d = models.FloatField()
    value_col_e = models.FloatField()
    value_col_f = models.FloatField()

    objects = DataFrameManager()

    def __unicode__(self):
        return "{} {} {} {} {} {}".format(self.row_col_a,
                                          self.row_col_b,
                                          self.row_col_c,
                                          self.value_col_d,
                                          self.value_col_e,
                                          self.value_col_f)
