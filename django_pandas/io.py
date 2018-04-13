from collections.abc import Mapping

import pandas as pd
from .utils import update_with_verbose, get_related_model
import django
from django.db.models import fields, ForeignKey
import numpy as np
try:
    from django.contrib.gis.db.models import fields as geo_fields
except (ImportError, django.core.exceptions.ImproperlyConfigured): # pragma: no cover
    geo_fields = None


def to_fields(qs, fieldnames):
    for fieldname in fieldnames:
        model = qs.model
        for fieldname_part in fieldname.split('__'):
            try:
                field = model._meta.get_field(fieldname_part)
            except django.db.models.fields.FieldDoesNotExist:
                try:
                    rels = model._meta.get_all_related_objects_with_model()
                except AttributeError:
                    field = fieldname
                else:
                    for relobj, _ in rels:
                        if relobj.get_accessor_name() == fieldname_part:
                            field = relobj.field
                            model = field.model
                            break
            else:
                model = get_related_model(field)
        yield field


def is_values_queryset(qs):
    if django.VERSION < (1, 9):
        return isinstance(qs, django.db.models.query.ValuesQuerySet)
    else:
        return qs._iterable_class == django.db.models.query.ValuesIterable


_FIELDS_TO_DTYPES = {
    fields.AutoField:                  np.dtype(np.int32),
    fields.BigAutoField:               np.dtype(np.int64),
    fields.BigIntegerField:            np.dtype(np.int64),
    fields.BinaryField:                object, # Pandas has no bytes type
    fields.BooleanField:               np.dtype(np.bool_),
    fields.CharField:                  object, # Pandas has no str type
    fields.DateField:                  np.dtype('datetime64[D]'),
    fields.DateTimeField:              np.dtype('datetime64[us]'),
    fields.DecimalField:               object,
    fields.DurationField:              np.dtype('timedelta64[us]'),
    fields.EmailField:                 object,
    fields.FilePathField:              object,
    fields.FloatField:                 np.dtype(np.float64),
    fields.GenericIPAddressField:      object,
    fields.IntegerField:               np.dtype(np.int32),
    fields.PositiveIntegerField:       np.dtype(np.uint32),
    fields.PositiveSmallIntegerField:  np.dtype(np.uint16),
    fields.SlugField:                  object,
    fields.SmallIntegerField:          np.dtype(np.int16),
    fields.TextField:                  object,
    fields.TimeField:                  object,
    fields.URLField:                   object,
    fields.UUIDField:                  object,

    # https://pandas.pydata.org/pandas-docs/stable/missing_data.html#missing-data-casting-rules-and-indexing
    # Explicitly setting NullBooleanField here can be removed when support for
    # Django versions <= 2.0 are dropped. See
    # https://github.com/django/django/pull/8467
    fields.NullBooleanField:           object,
}

if geo_fields is not None:
    _FIELDS_TO_DTYPES.update({
        # Geometry fields
        geo_fields.GeometryField:          object,
        geo_fields.RasterField:            object,
    })

def _get_dtypes(fields_to_dtypes, fields, fieldnames):
    """Infer NumPy dtypes from field types among those named in fieldnames.

    Returns a list of (fieldname, NumPy dtype) pairs. Read about NumPy dtypes
    here [#]_ and here [#]_. The returned list can be passed to ``numpy.array``
    in ``read_frame``.

    Parameters
    ----------

    field_to_dtypes : mapping
        A (potentially empty) mapping of Django field classes to NumPy dtypes.
        This mapping overrides the defualts from ``_FIELDS_TO_DTYPES``. The
        back-up default dtype is ``object`` for unfamiliar field classes.

    fields : list of Django field class instances
        They must correspond in order to the columns of the dataframe that
        ``read_frame`` is building.

    fieldnames : iterable of names of the fields as they will appear in the data
        frame

    .. [#] https://docs.scipy.org/doc/numpy/user/basics.types.html
    .. [#] https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
    """
    dtypes = []
    f2d = _FIELDS_TO_DTYPES.copy()
    f2d.update(fields_to_dtypes)
    for k, v in f2d.items():
        if not issubclass(k, django.db.models.fields.Field):
            raise TypeError('Expected a type of field, not {!r}'.format(k))
        if not isinstance(v, np.dtype):
            f2d[k] = np.dtype(v)
    for field, name in zip(fields, fieldnames):
        # Get field.null before switching to target field since foreign key can
        # be nullable even while the target isn't, and vice versa.
        nullable = field.null
        if isinstance(field, ForeignKey):
            field = field.target_field
        nullable = nullable or field.null

        # Find the lowest subclass among the keys of f2d
        t, dtype = object, np.generic
        for k, v in f2d.items():
            if isinstance(field, k) and issubclass(k, t):
                t, dtype = k, v

        # Handle nulls for integer and boolean types
        if nullable and issubclass(dtype.type, (np.bool_, bool)):
            # Pandas handles nullable booleans as objects. See
            # https://pandas.pydata.org/pandas-docs/stable/missing_data.html#missing-data-casting-rules-and-indexing
            # Not needed until Django 2.1. See
            # https://github.com/django/django/pull/8467
            dtype = np.object_
        elif nullable and issubclass(dtype.type, (np.integer, int)):
            # dtype.itemsize is denominated in bytes. Check it against the
            # number of mantissa bits since the max exact integer is
            # 2**(mantissa bits):
            #   >>> 2**sys.float_info.mant_dig - 1 == int(float(2**sys.float_info.mant_dig - 1))
            #   True
            #   >>> 2**sys.float_info.mant_dig     == int(float(2**sys.float_info.mant_dig))
            #   True
            #   >>> 2**sys.float_info.mant_dig + 1 == int(float(2**sys.float_info.mant_dig + 1))
            #   False
            # Thus the integer needs to fit into ((mantissa bits) - 1) bits
            # https://docs.scipy.org/doc/numpy-dev/user/basics.types.html
            def fits(itype, ftype):
                return np.iinfo(itype).bits <= (np.finfo(ftype).nmant - 1)
            if fits(dtype, np.float16):
                dtype = np.float16
            elif fits(dtype, np.float32):
                dtype = np.float32
            elif fits(dtype, np.float64):
                dtype = np.float64
            elif fits(dtype, np.longdouble):
                dtype = np.longdouble
            else:
                dtype = np.object_

        dtypes.append((name, dtype))
    return dtypes


def read_frame(qs, fieldnames=(), index_col=None, coerce_float=False,
               verbose=True, compress=False):
    """
    Returns a dataframe from a QuerySet

    Optionally specify the field names/columns to utilize and
    a field as the index

    This function uses the QuerySet's ``iterator`` method, so it does not
    populate the QuerySet's cache. This is more memory efficient in the typical
    case where you do not use the QuerySet after ``read_frame``.

    Parameters
    ----------

    qs: The Django QuerySet.
    fieldnames: The model field names to use in creating the frame.
         You can span a relationship in the usual Django way
         by using  double underscores to specify a related field
         in another model
         You can span a relationship in the usual Django way
         by using  double underscores to specify a related field
         in another model

    index_col: specify the field to use  for the index. If the index
               field is not in the field list it will be appended

    coerce_float : boolean, default False
        Attempt to convert values to non-string, non-numeric data (like
        decimal.Decimal) to floating point, useful for SQL result sets
        Does not work with ``compress``.

    verbose:  boolean If  this is ``True`` then populate the DataFrame with the
                human readable versions of any foreign key fields else use
                the primary keys values.
                The human readable version of the foreign key field is
                defined in the ``__unicode__`` or ``__str__``
                methods of the related class definition

    compress: a false value, ``True``, or a mapping, default False
        If a true value, infer NumPy data types [#]_ for Pandas dataframe
        columns from the corresponding Django field types. For example, Django's
        built in ``SmallIntgerField`` is cast to NumPy's ``int16``. If
        ``compress`` is a mapping (e.g., a ``dict``), it should be a mapping
        with Django field subclasses as keys and  NumPy dtypes [#]_ as values.
        This mapping overrides the defaults for the field classes appearing in
        the mapping. However, the inference is based on the field subclass
        lowest on a chain of subclasses, that is, in order of inheritance.
        To override ``SmallIntegerField`` it is therefore not sufficient to
        override ``IntegerField``. Careful of setting ``compress={}`` because
        ``{}`` is a false value in Python, which would cause ``read_frame``
        not to compress columns.

        Does not work with ``coerce_float``.

    Known Issues
    ------------

    When using ``compress=True`` with a nullable foreign key field the double-
    underscore import name may not work but the single-underscore import name
    should. For example, suppose model ``A`` has a nullable foreign key field
    ``b`` pointing at model ``B``, both of which models' primary key fields are
    called ``id``. Suppose further that ``A``'s table has some entries with
    null values of ``b`` and some with non-null values.
    ``read_frame(A.objects.all(), ['b', 'b_id'])`` and
    ``read_frame(A.objects.filter(b__isnull=False), ['b__id'])`` will work as
    expected, but ``read_frame(A.objects.all(), ['b__id'])`` will not.

    .. [#] https://docs.scipy.org/doc/numpy/user/basics.types.html
    .. [#] https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
   """
    if coerce_float and compress:
        raise ValueError('Cannot use coerce_float and compress at the same time')
    if fieldnames:
        fieldnames = pd.unique(fieldnames)
        if index_col is not None and index_col not in fieldnames:
            # Add it to the field names if not already there
            fieldnames = tuple(fieldnames) + (index_col,)
        fields = to_fields(qs, fieldnames)
    elif is_values_queryset(qs):
        if django.VERSION < (1, 9):
            if django.VERSION < (1, 8):
                annotation_field_names = qs.aggregate_names
            else:
                annotation_field_names = list(qs.query.annotation_select)

            if annotation_field_names is None:
                annotation_field_names = []

            extra_field_names = qs.extra_names
            if extra_field_names is None:
                extra_field_names = []

            select_field_names = qs.field_names

        else:
            annotation_field_names = list(qs.query.annotation_select)
            extra_field_names = list(qs.query.extra_select)
            select_field_names = list(qs.query.values_select)

        fieldnames = select_field_names + annotation_field_names + \
            extra_field_names
        fields = [None if '__' in f else qs.model._meta.get_field(f)
                  for f in select_field_names] + \
            [None] * (len(annotation_field_names) + len(extra_field_names))

        uniq_fields = set()
        fieldnames, fields = zip(
            *(f for f in zip(fieldnames, fields)
              if f[0] not in uniq_fields and not uniq_fields.add(f[0])))
    else:
        fields = qs.model._meta.fields
        fieldnames = [f.name for f in fields]

    if not issubclass(qs._iterable_class, django.db.models.query.ValuesListIterable):
        qs = qs.values_list(*fieldnames)
    recs = qs.iterator()

    if compress:
        if not isinstance(compress, (bool, Mapping)):
            raise TypeError('Ambiguous compress argument: {!r}'.format(compress))
        if not isinstance(compress, Mapping):
            compress = {}
        dtype = _get_dtypes(compress, fields, fieldnames)
        recs = np.array(list(recs), dtype=dtype)
    df = pd.DataFrame.from_records(recs, columns=fieldnames,
                                   coerce_float=coerce_float)

    if verbose:
        update_with_verbose(df, fieldnames, fields)

    if index_col is not None:
        df.set_index(index_col, inplace=True)

    return df
