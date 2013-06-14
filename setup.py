from setuptools import setup, find_packages


long_description = (
    open('README.rst').read() +
    open('CHANGES.rst').read() +
    open('TODO.rst').read()
)


setup(
    name='django-pandas',
    version='0.0.1',
    description='Tools for working with pandas in your Django projects',
    long_description=long_description,
    author='Christopher Clarke',
    author_email='cclarke@chrisdev.com',
    url='https://github.com/chrisdev/django-pands/',
    packages=find_packages(),
    install_requires=[
        'django>=1.4.5',
        'django-model-utils>=1.4.0',
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
)
