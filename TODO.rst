====
TODO
====

- Add coverage and tox and integrate with travis-CL
- Add to pivot_table method
2013-07-24
-----------
- We need to implement the pivot table method

- Can we bypass the ValuesListQuerySet and numpy_fromrecords and just use the
  DatatFrame.from_records with the tuple of sql records


2013-07-19
-----------
We thinking of implenenting the following API

-  **to\_dataframe** - the core method which returns a dataframe based
   on the columns that you specify you can also set the index column

   **Arguments**

   *cols*: the model fields to utilise in creating the frame. to span a
   relationship, just use the field name of related fields across
   models, separated by double underscores,

   *index*: the model field name to use for the index

   *coerce\_float*: The returned columns (except the index) will be
   floats. This may be required if the queryset returns lots of null
   values

-  **to\_timeseries** - A convenience method to create a pandas time
   series from a queryset

   **Arguments**

   *freq*: A string representing the pandas frequency or date offset

   *storage*: specify if your queryset uses the `wide` or `long` format for
   data.

   **wide format**

   :::

           date           gdp     inflation     wages

           2010-01-01   204966         2.0       100.7

           2010-02-02   204704          2.4       100.4

           2010-03-01   205966          2.5       100.5


   **long or stacked format**

   ::

           date        series_mame    value

           2010-01-01       gdp        204699

           2010-01-01       inflation   2.0

           2010-01-01       wages       100.7

           2010-02-01       gdp        204704

           2010-02-01       inflation   2.4

           2010-03-01       wages       100.4

           2010-02-01       gdp        205966

           2010-02-01       inflation   2.5

           2010-03-01       wages       100.5

   *pivot\_column:* This is required once the you specify ``long`` for
   the storage\_fmt. This could either be a list or string identifying
   the column name or combination of columns that contain the ‘pivot’
   identifying column. If your pivot\_column is a single column then the
   unique values in this column become new time series columns. If you
   sepecify a list of columns then the values in these columns are
   concatenated (using the '-' as a seperator and these values are used
   for the new timeseries columns

   *values*: Also required if you utilize the ``long`` storage the
   values column name is use for populating new frame’s values

   *fill\_na*: Fill in the missing values using the specifies method
   methods {'backfill, 'bill', 'pad', 'ffill'}

-  **to\_pivot\_table** - A convenience method to create a pivot table
   from the queryset

   *values*: column to aggregate

   *rows*: the list of column names to group on

   *cols*: list of column names to group on

   *aggfunc*: the function to uses in calculate the group aggregate

   *fill\_value*: the value to replace missing values with

   *margin*: boolean defalut False. Calculate subtotals/grand totals

   *dropna*: Do not include columns whoes entries are all NaN


