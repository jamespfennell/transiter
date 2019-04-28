.PHONY: docs test

clear-coverage:
	rm -f .coverage

all-tests: clear-coverage unit-tests db-tests

integration-tests:
	cd tests/integrationtest; make test

unit-tests:
	transiterclt rebuild-db --yes
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/unittests

db-tests:
	transiterclt rebuild-db --yes
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/dbtests

docs:
	cd docs; rm -r build; make html

run-gunicorn-server:
	gunicorn -w 4 -b 127.0.0.1:5000 transiter:wsgi_app

clean:
	rm -rf *.egg-info build dist .eggs .coverage
	cd tests/integrationtest; rm -rf *.egg-info build dist .eggs
