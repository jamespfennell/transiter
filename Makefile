.PHONY: docs test

integration-tests:
	cd tests/integrationtest; make test

docs:
	cd docs; rm -r build; make html

clean:
	git clean -dnX

black:
	pip install black
	black {transiter,tests,*py}

package:
	rm -f dist/*
	python setup.py sdist bdist_wheel

distribute:
	twine upload dist/*


unit-tests:
	rm -f .coverage
	pip install -r dev-requirements.txt
	nosetests --with-coverage --cover-package=transiter --rednose \
	    -v tests/unittests -v tests/dbtests

make unit-tests-in-docker-container:
	docker cp tests transiter-webserver:/transiter
	docker cp dev-requirements.txt transiter-webserver:/transiter/dev-requirements.txt
	docker cp Makefile transiter-webserver:/transiter/Makefile
	docker exec -w /transiter -it transiter-webserver make unit-tests
	docker cp transiter-webserver:/transiter/.coverage .coverage
