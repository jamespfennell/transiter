.PHONY: docs test

integration-tests:
	cd tests/integrationtest; python setup.py develop; make test

unit-tests:
	rm -f .coverage
	transiterclt rebuild-db --yes
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/unittests

docs:
	cd docs; rm -r build; make html

run-gunicorn-server:
	gunicorn -w 4 -b 127.0.0.1:5000 transiter:wsgi_app

clean:
	rm -rf *.egg-info build dist .eggs .coverage
	cd tests/integrationtest; rm -rf *.egg-info build dist .eggs
