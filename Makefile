.PHONY: docs test

DOCKER_BUILD=docker build

build-base:
	${DOCKER_BUILD} -f docker/Dockerfile -t jamespfennell/transiter:latest .

build-ci: build-base
	${DOCKER_BUILD} -f docker/ci.Dockerfile -t jamespfennell/transiter:latest-ci .

build: build-base

build-all: build-ci build


# The following commands are designed to be run in the CI Docker image as well as on bare metal

docs:
	cd docs; rm -r site; mkdocs build

distribute:
	twine upload /transiter/dist/*
	# For testing add  --repository-url https://test.pypi.org/legacy/ to the previous command

unit-tests:
	coverage run -a -m pytest tests/unit

db-tests:
	./docker/wait-for-it.sh $$TRANSITER_DB_HOST:$$TRANSITER_DB_PORT
	coverage run -a -m pytest tests/db

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
	docker-compose -p transiter -f tests/endtoend/compose.yaml up -d sourceserver
	docker-compose -p transiter -f tests/endtoend/compose.yaml run testrunner



# Misc commands

black:
	black {transiter,tests,*py}
