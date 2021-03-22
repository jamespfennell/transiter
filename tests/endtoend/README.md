# Transiter end to end tests

The end to end tests simulate real world usage of Transiter.
During the tests, Transiter is running as it would in production
and various standard operations (installing transit systems, performing feed updates,
 querying the resulting data)
are performed and verified.
Because the test closely resembles actual usage, it is extremely
valuable for ensuring the correctness of the software.

The end to end test is run automatically as a part of the 
continuous integration on Travis.

## Structure of the test

During a test run, there are three live components:

1. The Transiter instance, listening by default on port 8000.

1. A source server, which is used to simulate external transit agency data sources.
   This listens by default on port 5001.
    
1. The test driver itself. 
   It interacts with Transiter solely through Transiter's HTTP API.


## Running the test

The test requires a running Transiter instance
that is listening at the location given 
in the environment variable `TRANSITER_HOST`.
It also requires the source server to be running. 
The source server should be accessible to the test driver
at the location `SOURCE_SERVER_HOST` and be accessible
to the Transiter instance at the location `SOURCE_SERVER_HOST_WITHIN_TRANSITER`.
The defaults for these are:

- `TRANSITER_HOST=http://localhost:8000`

- `SOURCE_SERVER_HOST=http://localhost:5001`

- `SOURCE_SERVER_HOST_WITHIN_TRANSITER=SOURCE_SERVER_HOST`

There are three ways to setup the test,
and each corresponds to a different configuration 
for the environment variables.
In the following, it is assumed the the current working
directory is the root of the Transiter repo.

### Bare metal setup

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

