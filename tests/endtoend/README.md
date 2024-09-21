# Transiter end to end tests

In the end-to-end tests, Transiter is running as it would in production
    and various standard operations
    (installing transit systems, performing feed updates, querying the resulting data)
    are performed and verified.
Because the tests closely resemble actual usage, these tests are really
    valuable for ensuring Transiter's correctness.

The tests are written in Python, which is an artifact of Transiter originally being written in Python, too.
However, the intent is to keep the tests in Python because the language difference
  is nicely enforces that the tests don't use non-API aspects of Transiter.

## Structure of a test run

During a test run, there are four live components:

1. Postgres.

1. The Transiter instance, listening on its default ports.
    (In fact, the tests only use the admin HTTP service, which by default listens on 8082.)

1. A source server, which is used to simulate external transit agency data sources.
   This listens by default on port 8090.

1. The test driver itself. 
   It interacts with Transiter solely through Transiter's admin HTTP API.

## Running the tests

### Simplest way

If you are on a machine with Docker and Docker compose available,
    then run `just test-e2e`.

### Manual

The Python tests have some dependencies which need to be installed.
As usual, it's best to do this in a virtual env. Then:
```
pip install -r tests/endtoend/requirements.txt
```

Steps:

1. Ensure Postgres is running with a `transiter` database and a user/password `transiter`/`transiter`.

1. Run Transiter using `go run . server`.
    (You can also perform the test with different Postgres credentials or a different Postgres database name.
    You just need to provide these to the Go binary using the `--postgres-connection-string` flag.)

1. In another terminal, run the source server using `go run tests/endtoend/sourceserver/sourceserver.go`.

1. In another terminal, run the tests using `pytest path/to/test.py`.

**Advanced usage**
The test assumes there is a running Transiter instance with an HTTP admin service
listening at the location given in the environment variable `TRANSITER_HOST`.
It also requires the source server to be running. 
The source server should be accessible to the test driver
at the location `SOURCE_SERVER_HOST` and be accessible
to the Transiter instance at the location `SOURCE_SERVER_HOST_WITHIN_TRANSITER`.
The defaults for these are:

- `TRANSITER_HOST=http://localhost:8082` (this is also the Transiter default)

- `SOURCE_SERVER_HOST=http://localhost:8090`

- `SOURCE_SERVER_HOST_WITHIN_TRANSITER=SOURCE_SERVER_HOST`

So by default everything works without customization, but all of the ports/addresses
    can be customized if you need.

### Manual with Docker compose

Assuming the Docker image has been built locally with:

    docker build . -t jamespfennell/transiter:latest   

First launch Transiter, Postgres and the source server:

    docker compose -f tests/endtoend/compose.yml up --build sourceserver transiter db

Then in another terminal run the tests with either:

    docker compose -f tests/endtoend/compose.yml up --build testrunner

Or assuming all the Python dependencies are installed:

    SOURCE_SERVER_HOST_WITHIN_TRANSITER=http://sourceserver:8090 pytest

## Writing new tests

Best to cargo cult from the existing tests.
The tests in `test_shapes.py` and `test_routes.py` are particularly good and worth emulating.
