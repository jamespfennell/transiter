
# Transiter end to end test

The end to end test simulates real world usage of Transiter.
During the test, Transiter is running as it would in production
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
    
1. The test driver itself. The test driver is written in Python.
   It interacts with Transiter solely through Transiter's HTTP API.

The source server is a HTTP server with a simple REST API. 
(The code is in the `sourceserver` subdirectory.) 
For a given path, the source server provides GET, PUT and DELETE endpoints,
which satisfy standard REST semantics.
During the test, data - such as the content of a GTFS realtime feed -
is PUT on the source server by the test runner.
The Transiter instance is configured to update the relevant feed by performing
a GET request to the same URL.
By this mechanism the test customizes the input data to the test
while still running Transiter in production mode.



## Running the test

To perform the test it is necessary for the Transiter
 instance and the source server to be running.
It is assumed the Transiter database is empty at the beginning.
The test is run by executing the test driver.

The networking of these components is important:

- The test driver must be able to send requests to the source server, 
    in order to PUT data.
- The test driver must be able to send requests to the Transiter server -
    this is how the test is actually run.
- The Transiter server must be able to send requests to
    the source server, in order to GET data.
    

### Local development context

The Transiter instance can be launched in debug mode using the command line tools
facility:

```bash
transiterclt launch http-debug server
```
Assuming you are in the end to end test directory, the
source server can be launched with:
```bash
python sourceserver/main.py
```
Before running the test, ensure the database is empty:
```bash
transiterclt rebuild-db
```
The test driver is then invoked with:
```bash
python driver
```
### Docker container context

### Other contexts
