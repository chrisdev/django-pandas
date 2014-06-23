CHANGES
========

0.2.0 (2014-06-15)
--------------------

- Added the ``io`` module so that DataFrames can be created from any 
  queryset so you don't need to to add a ``DataFrame manager`` to your
  models. This is good for working with legacy projects.
- added a Boolean ``verbose`` argument to all methods (which defaults to ``True``)
  This populate the DataFrame columns with the human readable versions of 
  foreign key or choice fields.
- Improved the performance DataFrame creation by removing dependency on 
  ``np.core.records.fromrecords``
- Loads of bug fixes, more tests and improved coverage and better
  documentation`

