.PHONY: docs test
.ONESHELL:

webtest:
	python tests/webtest/feedserver.py &
	export TRANSITER_DB_NAME=transiter_web_test
	sleep 3
	python rebuilddb.py
	python -m transiter.endpoints.flaskapp &
	sleep 3
	kill $(lsof -t -i:5000)
	kill $(lsof -t -i:5001)


test:
	rm .coverage
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/unittests

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

