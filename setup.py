from setuptools import setup, find_packages


long_description = (
    open('README.rst').read() + '\n\n' +
    open('CHANGES.rst').read() +
    open('TODO.rst').read()
)


setup(
    name='django-pandas',
    version='0.0.2',
    description='Tools for working with pandas in your Django projects',
    long_description=long_description,
    author='Christopher Clarke',
    author_email='cclarke@chrisdev.com',
    url='https://github.com/chrisdev/django-pands/',
    packages=find_packages(),
    install_requires=[
        'Django>=1.4.5',
        'django-model-utils>=1.4.0',
        'pandas>=0.12.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
    ],
    zip_safe=False,
    tests_require=["Django>=1.4.5",
                   "numpy>=1.6.1",
                   "django-model-utils>-1.4.0",
                   "pandas>=0.12.0",
                   ],
    test_suite="runtests.runtests"

)
