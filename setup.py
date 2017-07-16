from setuptools import setup, find_packages


long_description = (
    open('README.rst').read() + '\n\n' +
    open('CHANGES.rst').read()
)
MAJOR = 0
MINOR = 4
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
        'Django>=1.4.2',
        'pandas>=0.14.1',
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
        'Framework :: Django',
    ],
    zip_safe=False,
    tests_require=[
        "Django>=1.4.2",
        "pandas==0.20.1",
        "coverage>=4.0",
                   ],
    test_suite="runtests.runtests"

)
