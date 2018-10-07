.PHONY: docs test

test:
	nosetests --with-coverage --cover-package=transiter --rednose -v tests

reset-db:
	python -m transiter.rebuilddb

reset-docs:
	cd docs; rm -r source; rm -r _build; sphinx-apidoc -o source ../transiter; make html

docs:
	cd docs; rm -r _build; make html

run-debug-server:
	export FLASK_APP=transiter/flaskapp.py; export FLASK_DEBUG=1; python -m flask run

run-gunicorn-server:
	gunicorn -w 4 -b 127.0.0.1:5000 transiter.flaskapp:app

