# Transiter end to end tests

The end to end tests simulate real world usage of Transiter.
In the tests, Transiter is running as it would in production
and various standard operations (installing transit systems, performing feed updates,
 querying the resulting data)
are performed and verified.
Because the test closely resembles actual usage, these tests are really
valuable for ensuring the correctness of the software.

The tests are written in Python, which is an artifact of Transiter originally being written in Python, too.
However, the intent is to keep the tests in Python because the language difference
  is nicely enforces that the tests don't use non-API aspects of Transiter.

## Structure of the test

During a test run, there are four live components:

1. Postgres.

1. The Transiter instance, listening on its default ports.

1. A source server, which is used to simulate external transit agency data sources.
   This listens by default on port 8090.

1. The test driver itself. 
   It interacts with Transiter solely through Transiter's admin HTTP API.

## Running the test

**Simplist way**: in the root of repo, run `bash tests/endtoend/run.sh`.

The test requires a running Transiter instance with an HTTP admin service
listening at the location given 
in the environment variable `TRANSITER_HOST`.
It also requires the source server to be running. 
The source server should be accessible to the test driver
at the location `SOURCE_SERVER_HOST` and be accessible
to the Transiter instance at the location `SOURCE_SERVER_HOST_WITHIN_TRANSITER`.
The defaults for these are:

- `TRANSITER_HOST=http://localhost:8082` (this is also the Transiter default)

- `SOURCE_SERVER_HOST=http://localhost:8090`

- `SOURCE_SERVER_HOST_WITHIN_TRANSITER=SOURCE_SERVER_HOST`

### Full Docker compose

The easiest way to run the tests is using Docker compose.
This assumes that Docker image has been built locally with:

    docker build . -t jamespfennell/transiter:latest   

First launch Transiter, Postgres and the source server:

    docker-compose -f tests/endtoend/compose.yml up --build sourceserver transiter db

Then in another terminal run the tests:

    docker-compose -f tests/endtoend/compose.yml up --build testrunner
