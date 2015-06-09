from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django_pandas.managers import DataFrameManager


@python_2_unicode_compatible
class MyModel(models.Model):
    index_col = models.CharField(max_length=1)
    col1 = models.IntegerField()
    col2 = models.FloatField(null=True)
    col3 = models.FloatField(null=True)
    col4 = models.IntegerField()

    def __str__(self):
        return "{} {} {} {}".format(
            self.index_col,
            self.col1,
            self.col2,
            self.col3,
            self.col4
        )


class MyModelChoice(models.Model):
    CHOICES = [
        (1, 'First'),
        (2, 'Second'),
        (3, 'Third'),
    ]
    col1 = models.IntegerField(choices=CHOICES)
    col2 = models.FloatField(null=True)
    objects = DataFrameManager()


@python_2_unicode_compatible
class DataFrame(models.Model):

    index = models.CharField(max_length=1)
    col1 = models.IntegerField()
    col2 = models.FloatField()
    col3 = models.FloatField()
    col4 = models.IntegerField()

    objects = DataFrameManager()

    def __str__(self):
        return "{} {} {} {}".format(
            self.index,
            self.col1,
            self.col2,
            self.col3,
            self.col4
        )


@python_2_unicode_compatible
class LongTimeSeries(models.Model):
    date_ix = models.DateTimeField()
    series_name = models.CharField(max_length=100)
    value = models.FloatField()

    objects = DataFrameManager()

    def __str__(self):
        return "{} {} {}".format(self.date_ix,
                                 self.series_name,
                                 self.value)


@python_2_unicode_compatible
class WideTimeSeries(models.Model):
    date_ix = models.DateTimeField()
    col1 = models.FloatField()
    col2 = models.FloatField()
    col3 = models.FloatField()
    col4 = models.FloatField()

    objects = DataFrameManager()

    def __str__(self):
        return "{} {} {} {}".format(
            self.date_ix,
            self.col1,
            self.col2,
            self.col3,
            self.col4
        )


@python_2_unicode_compatible
class PivotData(models.Model):
    row_col_a = models.CharField(max_length=15)
    row_col_b = models.CharField(max_length=15)
    row_col_c = models.CharField(max_length=15)
    value_col_d = models.FloatField()
    value_col_e = models.FloatField()
    value_col_f = models.FloatField()

    objects = DataFrameManager()

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5}".format(
            self.row_col_a, self.row_col_b, self.row_col_c,
            self.value_col_d, self.value_col_e, self.value_col_f
        )


@python_2_unicode_compatible
class Trader(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Security(models.Model):
    symbol = models.CharField(max_length=20)
    isin = models.CharField(max_length=20)

    def __str__(self):
        return "{0}-{1}".format(self.isin, self.symbol)


@python_2_unicode_compatible
class TradeLog(models.Model):
    trader = models.ForeignKey(Trader)
    symbol = models.ForeignKey(Security, null=True)
    log_datetime = models.DateTimeField()
    price = models.FloatField()
    volume = models.IntegerField()

    objects = DataFrameManager()

    def __str__(self):
        return "{0}-{1}-{2}-{3}-{4}".format(
            self.trader,
            self.symbol,
            self.log_datetime,
            self.price,
            self.volume
        )
