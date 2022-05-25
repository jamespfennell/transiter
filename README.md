# Transiter

Transiter is a backend web service that makes it easy to use transit data in web apps, 
    train arrival time boards and similar technologies.

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

## Getting started

To build Transiter you need to have Go 1.18 installed, 
    and to run it you need a Postgres instance.
If Docker is available you can easily spin up Postgres with:

```
docker run -e POSTGRES_USER=transiter -e POSTGRES_PASSWORD=transiter -e POSTGRES_DB=transiter -b 5432:5432 postgres
```

With the databse running, the Transiter _server_ is launched using:

```
go run . server
```

The HTTP API will now be available on `localhost:8080`.
You can also interact with the server using Transiter _client_ commands; 
    for example to list all installed transit system run:

```
go run . list
```

This will show that there are no transit systems installed, 
    and the next step is install one!
If you have an MTA API key you can install the NYC Subway:

```
go run . install --arg mta_api_key=$MTA_API_KEY -f us-ny-subway systems/us-ny-subway.yaml
```

The server logs will show that GTFS feed updates are happening, and the HTTP API will be populated with data.
To get data about the Rockefeller Center station, say, visit:

```
localhost:8080/systems/us-ny-subway/stops/D15
```

## Development

Transiter uses [sqlc](https://github.com/kyleconroy/sqlc)
    for generating database access methods.
The schema and queries are stored in the `db` directory and the Go files are generated using:

```
sqlc generate
```

Transiter uses [gRPC](https://grpc.io/) for developing the API.
The HTTP REST API is generated automatically using annotations in the proto files.
[Buf](https://github.com/bufbuild/buf) is used for compiling the proto files to the Go code:
```
buf generate
```
