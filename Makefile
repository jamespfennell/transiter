test:
	nosetests --with-coverage --cover-package=transiter --rednose -v tests

refresh-db:
	python -m transiter.rebuilddb

refresh-docs:
	cd docs; rm -r source; sphinx-apidoc -o source ../transiter; make html
