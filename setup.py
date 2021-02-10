import codecs
from setuptools import setup, find_packages


long_description = (
    codecs.open('README.rst', 'r', 'utf-8').read() + '\n\n' +
    codecs.open('CHANGES.rst', 'r', 'utf-8').read()
)
MAJOR = 0
MINOR = 6
MICRO = 4

VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

setup(
    name='django-pandas',
    version=VERSION,
    description='Tools for working with pydata.pandas in your Django projects',
    long_description=long_description,
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
        'Framework :: Django',
    ],
    zip_safe=False,
    tests_require=[
        "pandas>=0.20.1",
        "coverage>=4.0",
        "semver==2.10.1"
                   ],
    test_suite="runtests.runtests"

)
