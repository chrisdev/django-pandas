CHANGES
========
0.6.5 (2021-10-15)
------------------
This version added support for Pandas >=1.3 (thanks to @graingert)
Other Changes:
*  Migrated from Travis to Github Actions for CI (also @graingert)

* Avoid the use of deprecated methods `#139`_ and `#142`_ (again much thanks @graingert)

* Fix for issue `#135`_(Thanks @Yonimdo)

* Silence Django 3.2 errors on testing on etc. `#133`_ thanks @whyscream.

.. _`#139`: https://github.com/chrisdev/issues/135
.. _`#142`: https://github.com/chrisdev/issues/142
.. _`#135`: https://github.com/chrisdev/issues/135
.. _`#133`: https://github.com/chrisdev/issues/133

0.6.4 (2021-02-08)
------------------
Bumped version number as the previous release was incorrectly uploaded
to pypi

0.6.1 (2020-05-26)
------------------
Supports the latest release of Pandas 1.0.3

0.6.0 (2019-01-11)
------------------
Removes compatibility with Django versions < 1.8


0.5.2 (2019-01-3)
-----------------
**This is the last version that supports Django < 1.8**

- Improved coerce_float option (thanks @ZuluPro )
- Ensure compatibility with legacy versions of Django ( < 1.8)
- Test pass with Django 2+ and python 3.7

0.5.1 (2018-01-26)
-------------------
- Address Unicode decode error when installing with pip3 on docker (Thanks @utapyngo)

0.5.0 (2018-01-20)
------------------
- Django 2.0 compatibility (Thanks @meirains)

0.4.5 (2017-10-4)
-----------------
- A Fix for fieldname deduplication bug thanks to @kgabbott

0.4.4 (2017-07-16)
-------------------
- The `verbose` argument now handles more use cases (Thanks to @henhuy and
  Kevin Abbott)
- Corece float argument add to ```to_timeseries()``` method (Thanks Yousuf Jawwad)

0.4.3 (2017-06-02)
--------------------
- Fix doc typos and formatting
- Prevent column duplication in read_frame (Thanks Kevin Abbott)

0.4.2 (2017-05-22)
--------------------
- Compatibility with `pandas 0.20.1`
- Support for Python 2.7 and 3.5 with Django versions 1.8+
- Suport for Python 3.6 and Django 1.11
- We still support legacy versions (Python 2.7 and Django 1.4)

0.4.1 (2016-02-05)
-------------------
- Address the incompatibility with Django 1.9 due to the removal of
  specialized query sets like the
  `ValuesQuerySet <https://code.djangoproject.com/ticket/24211>`_
- Address the removal of the ``PassThrougManager`` from  ``django-model-utils``
  version ``2.4``.  We've removed the dependency on django-model-utils and
  included the PassThroughManger (which was always a standalone tool
  distributed a part of django-model-utils) for compatibility with
  earlier versions of Django (<= 1.8). For more recent versions of
  Django we're using Django's built in ``QuerySet.as_manager()``.
- Now supports Pandas 0.14.1 and above
- The fall in Coverage in this release largely reflects the integration of
  the PassThroughManager into the code base. We'll add the required test
  coverage for the PassThroughManager in subsequent releases.

0.3.1 (2015-10-25)
-------------------
- Extends the ability to span a ForeignKey relationship with double underscores
  to OneToOneField too thanks to Safe Hammad
- Provide better support for  ManyToMany and OneToMany relations thanks to
  Jeff Sternberg and @MiddleFork

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
  documentation
