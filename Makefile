.PHONY: docs test

integration-tests:
	cd tests/integrationtest; python setup.py develop
	python -m unittest discover tests/integrationtest

unit-tests:
	rm -f .coverage
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/unittests

rebuild-db:
	python rebuilddb.py

reset-docs:
	cd docs; rm -r source; rm -r _build; sphinx-apidoc -o source ../transiter; make html

docs:
	cd docs; rm -r build; make html

run-debug-server:
	export FLASK_APP=transiter/http/flaskapp.py; export FLASK_DEBUG=1; python -m flask run

run-gunicorn-server:
	gunicorn -w 4 -b 127.0.0.1:5000 transiter.http.flaskapp:app

run-task-server:
	python -m transiter.taskserver.server

clean:
	rm -rf *.egg-info build dist .eggs .coverage
	cd tests/integrationtest; rm -rf *.egg-info build dist .eggs
