test:
	nosetests --with-coverage --rednose -v tests

refresh-db:
	python -m transiter.rebuilddb
