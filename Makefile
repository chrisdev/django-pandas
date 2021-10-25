.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc
	rm -fr htmlcov/

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

develop:
	pip install -e .[test]

lint:
	flake8 django_pandas tests

test: develop
	python runtests.py

test-all:
	tox

coverage: develop
	coverage run --source django_pandas runtests.py
	coverage report -m
	coverage html
	open htmlcov/index.html

docs:
	rm -rf docs/django_pandas.rst
	rm -f docs/django_pandas.tests.rst
	sphinx-apidoc -o docs django_pandas
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python3 -m build
  python3 -m twine upload --repository pypi dist/*

test-release:clean
	python3 -m build
  python3 -m twine upload --repository tespypi dist/*

dist: clean
	python3 -m build
	ls -l dist
