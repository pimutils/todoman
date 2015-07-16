test:
	py.test

install-dev:
	pip install pytest flake8

stylecheck:
	flake8 .
