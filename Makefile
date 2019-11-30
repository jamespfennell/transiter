.PHONY: docs test

DOCKER_BUILD=docker build

build-base:
	${DOCKER_BUILD} -f docker/dockerfiles/base.Dockerfile -t jamespfennell/transiter:latest-base .

build-ci: build-base
	${DOCKER_BUILD} -f docker/dockerfiles/ci.Dockerfile -t jamespfennell/transiter:latest-ci .

build: build-base
	${DOCKER_BUILD} -f docker/dockerfiles/webserver.Dockerfile -t jamespfennell/transiter:latest-webserver .
	${DOCKER_BUILD} -f docker/dockerfiles/taskserver.Dockerfile -t jamespfennell/transiter:latest-taskserver .
	${DOCKER_BUILD} -f docker/dockerfiles/postgres.Dockerfile -t jamespfennell/transiter:latest-postgres .

build-all: build-ci build


# The following commands are designed to be run in the CI Docker image as well as on bare metal

docs:
	cd docs; rm -r site; mkdocs build

distribute:
	twine upload /transiter/dist/*
	# For testing add  --repository-url https://test.pypi.org/legacy/ to the previous command

unit-tests:
	pytest --cov=transiter --cov-config=.coveragerc --cov-append tests/unit

db-tests:
	./docker/wait-for-it.sh $$TRANSITER_DB_HOST:$$TRANSITER_DB_PORT
	pytest --cov=transiter --cov-config=.coveragerc --cov-append tests/db

nothing:
	echo "Available Transiter CI Docker image commands: docs, distribute, unit-tests, db-tests"


# The following commands are designed to be run on the bare metal system
# running the docker

containerized-unit-tests:
	docker-compose -p ci -f docker/ci-docker-compose.yml up --exit-code-from unit-tests unit-tests

containerized-db-tests:
	docker-compose -p ci -f docker/ci-docker-compose.yml up -d postgres-db-tests
	docker-compose -p ci -f docker/ci-docker-compose.yml up --exit-code-from db-tests db-tests

end-to-end-tests:
	cd tests/endtoend; python dockerdriver.py


# Misc commands

black:
	black {transiter,tests,*py}
