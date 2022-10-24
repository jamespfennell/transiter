#!/bin/bash
set -e

docker-compose -f tests/endtoend/compose.yml down

docker build . -t jamespfennell/transiter:latest

docker-compose -f tests/endtoend/compose.yml up --build --detach sourceserver transiter db

set +e
docker-compose -f tests/endtoend/compose.yml up --build --exit-code-from testrunner testrunner
RESULT=$?
set -e

docker-compose -f tests/endtoend/compose.yml down

exit $RESULT
