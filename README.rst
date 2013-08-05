==============
Django Pandas
==============
Tools for working with `pandas <http://pandas.pydata.org>`_ in your Django project

Contributors
============
* `Christopher Clarke <https://github.com/chrisdev>`_

Dependencies
=============
``django-pandas`` supports `Django`_ 1.4.7 or later and 
requires `django-model-utils`_. 
You will of course have to install ``Pandas`` and its dependencies such as 
``Numpy`` and optionally the 
other parts of the Scipy stack. You may wish to consult 
http://www.scipy.org/install.html for more information on installing the 
``Scipy`` stack. 

.. _Django: http://djangoproject.com/
.. _django-model-utils: http://pypi.python.org/pypi/django-model-utils

Installation
=============
Start by creating a new ``virtualenv`` for your project ::

    mkvirtualenv myproject

Next install ``numpy`` and optionally ``pandas`` ::

    pip install numpy
    pip install pandas

You may want to consult  the `scipy documentation`_ for more information 
on installing the ``Scipy`` stack.

.. _scipy documentation: http://www.scipy.org/install.html

Finally, install the development version of ``django-pandas``  
from the github repository using ``pip``::
    
    pip install https://github.com/chrisdev/django-pandas/tarball/master

Usage
======
To use ``django-pandas`` in your Django project, modify the ``INSTALLED_APPS``
in your settings module to include ``django_pandas``. 

DataFrameManager
----------------
``django-pandas`` provides a custom manager to use with models that
you want to render as Pandas Dataframes. The ``DataFrameManager``
manager provides the ``to_dataframe`` method that returns 
your models queryset as a Pandas DataFrame. To use the DataFrameManager, first
override the default manager in your model's definition 
as shown in the example below ::
    
    #models.py

    from django_pandas.managers import DataFrameManager

    class MyModel(models.Model):

        full_name = models.CharField(max_length=25)
        age = models.IntegerField()
        department = models.CharField(max_length=3)
        wage = models.FloatField()

        objects = DataFrameManager()

Create a dataframe from the objects in your model as follows ::

    df = MyModel.to_dataframe()

The ``to_datafame`` method supports the following arguments:

  - *fields*: Create the dataframe from the field specified

  - *index_field*: specify the field to use  for the index.
    If the index field is not in the field list it will be appended

  - *freq*: assumes that the index is a date_time stamp and converts it
        to the specified frequency

  - *fill_method*: specify a fill_method for your missing observation

**Note**: The current API is based on an internal project and 
will be changing soon but here are some examples of usage ::

    qs = MyData.objects.all()

To create a DataFrame only from selcted fields::
    
    MyData.to_dataframe('age', 'department', 'wage')

To set ``full_name`` as the index ::

     MyData.to_dataframe('age', 'department', 'wage', index='full_name')

You can use filters and excludes ::

    MyData.filter(age__gt=20, department='IT').to_dataframe(index='full_name')

.. end-here
