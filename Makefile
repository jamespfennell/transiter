test:
	nosetests --with-coverage --rednose -v

refresh-db:
	python -m transiter.rebuilddb
