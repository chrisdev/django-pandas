from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django_pandas.managers import DataFrameManager, PassThroughManager


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
class WideTimeSeriesDateField(models.Model):
    date_ix = models.DateField()
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
class TradeLogNote(models.Model):
    note = models.TextField()

    def __str__(self):
        return self.note


@python_2_unicode_compatible
class TradeLog(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Security, null=True, on_delete=models.CASCADE)
    log_datetime = models.DateTimeField()
    price = models.FloatField()
    volume = models.IntegerField()
    note = models.OneToOneField(TradeLogNote, on_delete=models.CASCADE)

    objects = DataFrameManager()

    def __str__(self):
        return "{0}-{1}-{2}-{3}-{4}-{5}".format(
            self.trader,
            self.symbol,
            self.log_datetime,
            self.price,
            self.volume,
            self.note
        )

@python_2_unicode_compatible
class Portfolio(models.Model):
    name = models.CharField(max_length=20)
    securities = models.ManyToManyField(Security)

    def __str__(self):
        return self.name


class DudeQuerySet(models.query.QuerySet):
    def abiding(self):
        return self.filter(abides=True)

    def rug_positive(self):
        return self.filter(has_rug=True)

    def rug_negative(self):
        return self.filter(has_rug=False)

    def by_name(self, name):
        return self.filter(name__iexact=name)


class AbidingManager(PassThroughManager):
    def get_queryset(self):
        return DudeQuerySet(self.model).abiding()

    get_query_set = get_queryset

    def get_stats(self):
        return {
            "abiding_count": self.count(),
            "rug_count": self.rug_positive().count(),
        }


class Dude(models.Model):
    abides = models.BooleanField(default=True)
    name = models.CharField(max_length=20)
    has_rug = models.BooleanField(default=False)

    objects = PassThroughManager(DudeQuerySet)
    abiders = AbidingManager()


class Car(models.Model):
    name = models.CharField(max_length=20)
    owner = models.ForeignKey(Dude, related_name='cars_owned', on_delete=models.CASCADE)

    objects = PassThroughManager(DudeQuerySet)


class SpotManager(PassThroughManager):
    def get_queryset(self):
        return super(SpotManager, self).get_queryset().filter(secret=False)

    get_query_set = get_queryset


class SpotQuerySet(models.query.QuerySet):
    def closed(self):
        return self.filter(closed=True)

    def secured(self):
        return self.filter(secure=True)


class Spot(models.Model):
    name = models.CharField(max_length=20)
    secure = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    secret = models.BooleanField(default=False)
    owner = models.ForeignKey(Dude, related_name='spots_owned', on_delete=models.CASCADE)

    objects = SpotManager.for_queryset_class(SpotQuerySet)()
