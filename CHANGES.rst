CHANGES
========

0.3.0 (2015-06-16)
---------------------
- This version supports Django 1.8
- Support for Pandas 0.16

0.2.2 (2015-03-02)
---------------------
- Added Support for Django 1.7

0.2.1 (2015-01-28)
---------------------
- Added Support for Values QuerySets 
- Support for Python 2.6
- Note we still have limited support for Django 1.7 but this will be coming in
  the next release

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

