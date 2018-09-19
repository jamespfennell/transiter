test:
	nosetests --with-coverage --cover-package=transiter --rednose -v tests

refresh-db:
	python -m transiter.rebuilddb
