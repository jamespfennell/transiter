.PHONY: docs test

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


python-tests:
	rm -f .coverage
	pip -q install -r dev-requirements.txt
	nosetests --with-coverage --cover-package=transiter --rednose \
	    -v tests/unit -v tests/db

make python-tests-in-docker-container:
	docker cp tests transiter-webserver:/transiter
	docker cp dev-requirements.txt transiter-webserver:/transiter/dev-requirements.txt
	docker cp Makefile transiter-webserver:/transiter/Makefile
	docker exec -w /transiter -it transiter-webserver make python-tests
	docker cp transiter-webserver:/transiter/.coverage .coverage
