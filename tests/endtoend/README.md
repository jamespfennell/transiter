# Transiter end to end tests

The end to end tests simulate real world usage of Transiter.
In the tests, Transiter is running as it would in production
and various standard operations (installing transit systems, performing feed updates,
 querying the resulting data)
are performed and verified.
Because the test closely resembles actual usage, it is extremely
valuable for ensuring the correctness of the software.

The tests are written in Python.
This is an artifact of Transiter originally being written in Python too.
However, the intent is to keep the tests in Python because the language difference
  is nicely enforces that the tests don't use non-API aspects of Transiter.


## Structure of the test

During a test run, there are three live components:

1. The Transiter instance, listening on its default ports.

1. A source server, which is used to simulate external transit agency data sources.
   This listens by default on port 8090.
    
1. The test driver itself. 
   It interacts with Transiter solely through Transiter's admin HTTP API.


## Running the test

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

There are three ways to setup the test,
and each corresponds to a different configuration 
for the environment variables.
In the following, it is assumed the the current working
directory is the root of the Transiter repo.

### Bare metal run

In this setup, the processes composing the Transiter instance
are run using the appropriate `transiterclt launch` command.
The Transiter instance will listen on `localhost`'s 8000 port.
The source server is run using the command `python sourceserver.py`,
 and will listen on `localhost`'s 5001 port.
As such, for this setup, the environment variables should be set to their defaults.

This test setup is tedious to create because you may need to have a few terminal windows open.
The benefit of it is that it's easy to pick up code changes to the Transiter production code,
unlike the Docker based solutions below.

The tests are run using,

    pytest tests/endtoend


### Partial Docker compose setup

In this setup, the Transiter processes and the source server are 
run in the same Docker compose network, and the test runner is outside of the network (i.e., bare metal).
This setup is ideal when writing new end to end tests that
    won't involve code changes to the Transiter production code.

First, the Docker compose network is launched using,
    
    docker-compose -p transiter -f docker/docker-compose.yml -d up 
    docker-compose -p transiter -f tests/endtoend/compose.yaml up -d sourceserver

The non-default environment variables should be set as follows:

    export SOURCE_SERVER_HOST_WITHIN_TRANSITER=http://sourceserver:5001
    
The tests are then run using,

    pytest tests/endtoend

### Full Docker compose 

This is the setup the tests run under in Travis CI.

First, the Docker compose network is launched using,
    
    docker-compose -p transiter -f docker/docker-compose.yml up -d 
    docker-compose -p transiter -f tests/endtoend/compose.yaml up -d sourceserver

And then the tests are run using,

    docker-compose -p transiter -f tests/endtoend/compose.yaml run testrunner

