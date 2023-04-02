# Transiter

Transiter is a backend web service that makes it easy to use transit data in web apps, 
    arrival time boards and similar technologies.

Transiter subscribes to GTFS static and realtime feeds
    and provides integrated views of the data through a REST API.
The endpoint for a particular stop, for example, returns the stop's static data 
    (such as its name and GPS coordinates), 
    its realtime data 
    (the list of vehicles that will arrive next, and the times they will arrive), 
    as well as derived data that Transiter computes automatically,
    such as which routes usually call at the stop.

You can get a sense for the data that's available by navigating
    through the [live demo site](https://demo.transiter.dev).
Transiter has a [dedicated documentation website](https://docs.transiter.dev)


**Project status**: a
    [migration from Python to Go](https://jpfennell.com/posts/transiter-python-go)
    was recently merged into mainline.
There are still some features missing in the Go version
    and adding these is being tracked in 
    [issue #87](https://github.com/jamespfennell/transiter/issues/87).
The Python version of Transiter can be viewed in 
    [this archived GitHub repository](https://github.com/jamespfennell/transiter-python).

## Getting started

Transiter uses Postgres for storing data,
    and by default assumes the database/user/password is `transiter`/`transiter`/`transiter`.
If Docker compose is available you can easily spin up a Postgres instance with this configuration from the root of the repo:

```
docker-compose up postgres
```

Transiter is written in Go.
With Go installed and the database running, the Transiter _server_ is launched using:

```
go run . server
```

Transiter's HTTP API will now be available on `localhost:8080`.
You can also interact with the server using Transiter _client_ commands.
For example to list all installed transit system run:

```
go run . list
```

This will show that there are no transit systems installed, 
    and the next step is install one!

**NY/NJ PATH train**:

```
go run . install -f us-ny-path systems/us-ny-path.yaml
```

**New York City subway**: If you have an [MTA API key](https://api.mta.info/#/landing):

```
go run . install --arg mta_api_key=$MTA_API_KEY -f us-ny-subway systems/us-ny-subway.yaml
```

In either case, the server logs will show that GTFS feed updates are happening,
    and the HTTP API will be populated with data.
If you installed the NYC subway, to get data about the Rockefeller Center station visit:

```
localhost:8080/systems/us-ny-subway/stops/D15
```

[Transiter's documentation website](https://docs.transiter.dev) has much more information,
    including how to run Tranister with Docker and how to use a non-default Postgres configuration.


## Development

Transiter uses [sqlc](https://github.com/kyleconroy/sqlc)
    for generating database access methods.
The schema and queries are stored in the `db` directory.
The Go files are generated using the following command in the repo root:

```
sqlc --experimental generate
```

Transiter uses [gRPC](https://grpc.io/) for developing the API.
The HTTP REST API is generated automatically using annotations in the proto files.
[Buf](https://github.com/bufbuild/buf) is used for compiling the proto files to the Go code:
```
buf generate
```
