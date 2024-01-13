# Transiter

Transiter is a program that makes it easy to use realtime transit data.
Instead of figuring out how to parse data from your local transit agency,
    you can run Transiter and access the data using a straightforward HTTP API.
Using Transiter as a backend, you can build things like
    web apps ([realtimerail.nyc](https://realtimerail.nyc), [closingdoors.nyc](https://closingdoors.nyc))
    and arrival time boards.

Transiter subscribes to GTFS static and realtime feeds
    and provides integrated views of the data through a HTTP REST API.
The [endpoint for a particular stop](https://demo.transiter.dev/systems/us-ny-subway/stops/L03), for example, returns:

- the stop's static data (such as its name and GPS coordinates), 

- the stop's realtime data (the list of vehicles that will arrive next, and the times they will arrive), 

- and derived data that Transiter computes automatically,
    such as which routes usually call at the stop.

You can get a sense for the data that's available by navigating
    through the [live demo site](https://demo.transiter.dev).
Transiter has a [WIP documentation website](https://docs.transiter.dev)


## Getting started

Transiter uses Postgres for storing data,
    and by default assumes the database/user/password is `transiter`/`transiter`/`transiter`.
These values can all be configured.
If you have Docker compose,
    you can easily spin up a Postgres instance with the default configuration from the root of the repo:

```
docker-compose up postgres
```

Transiter is written in Go.
To build Transiter and install it simply run:

```
go install .
```

After this, the Transiter _server_ is launched using:

```
transiter server
```

Transiter's HTTP API will now be available on `localhost:8080`.
In addition to the HTTP API, you can interact with the server using Transiter _client_ commands.
For example to list all installed transit system run:

```
transiter list
```

This will show that there are no transit systems installed.
The next step is install one!

**NY/NJ PATH train**:

```
transiter install -f us-ny-path systems/us-ny-path.yaml
```

**New York City subway**: If you have an [MTA API key](https://api.mta.info/#/landing):

```
transiter install --arg mta_api_key=$MTA_API_KEY -f us-ny-subway systems/us-ny-subway.yaml
```

In either case, the server logs will show that GTFS feed updates are happening,
    and the HTTP API will be populated with data.
If you installed the NYC subway, to get data about the Rockefeller Center station visit:

```
localhost:8080/systems/us-ny-subway/stops/D15
```


## Development guide

This is a guide for those who are interested in developing Transiter.
PRs are very welcome.

### Dev requirements

The basic requirements are the same as for running Transiter,
    Postgres 14+ and Go 1.18+.
Additionally, the project uses the [command runner tool Just](https://just.systems).
Installing Just is optional: as an alternative,
    you can always manually run the commands in the justfile.
However we think Just is great, and the rest of this guide assumes you've installed it.
Finally, having Docker available makes it really easy to run some other things locally
    but is totally optional.

### Changing the code

If you just change the Go code, you can build the code using `go build .`
    and run all the unit tests using `go test ./...` or `just test`.
Note that the unit tests assume Postgres is up and use Postgres for a bunch of DB tests.

If you have Docker installed you can also run all the Python E2E tests by running `just test-e2e`.
(The command `just test-all` runs both the unit and E2E tests).
The E2E tests are in the `tests/endtoend` directory.
Without Docker it's still possible to run the E2E tests following the instructions in that directory.
However the E2E tests also run on the GitHub actions CI and it's perhaps easiest to rely on that.
The E2E tests generally don't break unless you've introduced a regression.
For new major features it's great to add new E2E tests.

Like many Go projects Transiter relies on some code generation:

- Transiter uses [sqlc](https://github.com/kyleconroy/sqlc)
    for generating all of the DB interaction code.
    The DB schema and queries are stored in the `db` directory.

- Transiter uses [gRPC](https://grpc.io/) for developing the API.
    The HTTP REST API is generated automatically using annotations in the proto files.
    [Buf](https://github.com/bufbuild/buf) is used for compiling the proto files to the Go code.

If you make any changes to the API (`.proto` files) or DB SQL statements (`.sql` files),
    you'll need to run the code generation tools.

First install the tools:
```
just install-tools
```

Then run the code generation:

```
just generate
```
