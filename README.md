# Transiter

Transiter is a backend web service that makes it easy to use realtime transit data.
Transiter can be used to build things like
    web apps ([realtimerail.nyc](https://realtimerail.nyc), [closingdoors.nyc](https://closingdoors.nyc))
    and arrival time boards,
    and query transit data from other applications.

Transiter subscribes to GTFS transit data feeds from different transit agencies
    and provides integrated views of the data through a HTTP REST API.
The [endpoint for each station](https://demo.transiter.dev/systems/us-ny-subway/stops/L03), for example, provides:

- the station's static data (such as its name and GPS coordinates), 

- the station's realtime data (the list of vehicles that will arrive next, and the times they will arrive), 

- and derived data that Transiter computes automatically,
    such as which routes usually call at the station.

You can get a sense for the data that's available by navigating
    through the [live demo site](https://demo.transiter.dev),
    or by interacting with it programmatically:

```python
# Python snippet that finds the next train at the Rockefeller Center NYC subway station
import requests, time
data = requests.get("https://demo.transiter.dev/systems/us-ny-subway/stops/D15").json()
firstStopTime = data["stopTimes"][0]
secondsToLeave = int(firstStopTime["departure"]["time"]) - time.time()
print(f'The next train leaves in {int(secondsToLeave)} seconds and goes to {firstStopTime["trip"]["destination"]["name"]}.')
```

The [Transiter tour](https://docs.transiter.dev/tour/) contains many
    more examples like this.

Note that the demo site is best effort!
In general if you want to use Transiter for an application
    you will run and own [your own Transiter deployment](https://docs.transiter.dev/deployment).

## Quickstart guide

This is a whirlwind version of the [Transiter tour](https://docs.transiter.dev/tour/)
    on the [documentation website](https://docs.transiter.dev/).

Transiter uses Postgres for persisting data, and requires Postgres to have the PostGIS Postgres extension
By default Transiter assumes the database/user/password is `transiter`/`transiter`/`transiter`,
    but all these values can be configured.
If you have Docker installed,
    you can easily spin up the right kind of Postgres instance
    by running the following command:

```
docker run \
    -e POSTGRES_USER=transiter -e POSTGRES_PASSWORD=transiter -e POSTGRES_DB=transiter \
    -p 0.0.0.0:5432:5432 \
    postgis/postgis:14-3.4
```

Transiter is written in Go.
To build Transiter and install it run:

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

**San Francisco area BART**:

```
transiter install us-ca-bart
```

**New York City subway**: If you have an [MTA API key](https://api.mta.info/#/landing):

```
transiter install --arg mta_api_key=$MTA_API_KEY us-ny-subway
```

In either case, the server logs will show that GTFS feed updates are happening,
    and the HTTP API will be populated with data.
If you installed the BART, you can get data about the Embarcadero station by visiting:

```
localhost:8080/systems/us-ca-bart/stops/place_EMBR
```

## Development guide

This is a guide for people who are interested in developing Transiter.
PRs are very welcome!

### Dev requirements

The basic requirements are the same as for running Transiter,
    Postgres 14+ with PostGIS and Go 1.18+.
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

### Creating a release

Releases are created in the GitHub UI.
The release number `vX.Y.Z` must match the contents of the file `internal/version/BASE_VERSION`.
In the releases UI:

- Use a new tag with name `vX.Y.Z`.
- Set the release name to `vX.Y.Z`.
- Mark the release as a pre-release. 
    The goreleaser infrastructure will automatically promote it to a full release
    when the assets are pushed.

After the release is created, bump the version number in `internal/version/BASE_VERSION`
    and commit to mainline.

## License

MIT
