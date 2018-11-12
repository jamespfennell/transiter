.PHONY: docs test
.ONESHELL: integration-test

integration-test:
	python -m unittest discover tests/integrationtest

unit-tests:
	rm -f .coverage
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/unittests

test: unit-tests

reset-db:
	python rebuilddb.py

reset-docs:
	cd docs; rm -r source; rm -r _build; sphinx-apidoc -o source ../transiter; make html

docs:
	cd docs; rm -r _build; make html

run-debug-server:
	export FLASK_APP=transiter/endpoints/flaskapp.py; export FLASK_DEBUG=1; python -m flask run

run-gunicorn-server:
	gunicorn -w 4 -b 127.0.0.1:5000 transiter.endpoints.flaskapp:app

