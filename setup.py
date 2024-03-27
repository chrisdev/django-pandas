import codecs
from setuptools import setup, find_packages


long_description = (
    codecs.open('README.rst', 'r', 'utf-8').read() + '\n\n' +
    codecs.open('CHANGES.rst', 'r', 'utf-8').read()
)
MAJOR = 0
MINOR = 6
MICRO = 7 

VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

setup(
    name='django-pandas',
    version=VERSION,
    description='Tools for working with pydata.pandas in your Django projects',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Christopher Clarke',
    author_email='cclarke@chrisdev.com',
    url='https://github.com/chrisdev/django-pandas/',
    packages=find_packages(),
    install_requires=[
        'pandas>=0.14.1',
        'six>=1.15.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Framework :: Django',
    ],
    zip_safe=False,
    extras_require={
        "test": [
        "pandas>=0.20.1",
        "coverage==5.4",
        "semver==2.10.1"
                   ],
    },
)
