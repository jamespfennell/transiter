# Beginner's guide

The beginner's guide walks you through setting up Transiter,
  and then does a tour of some of transit data that's available in the Transiter API.

## Setup Postgres

Transiter uses Postgres for persisting data.
The Postgres instance must has the PostGIS Postgres extension installed.
Transiter uses PostGIS for storing geographic data (like the GPS location of stations)
  and for performing efficient queries on that data (such as finding the nearest stations of a particular point).

By default Transiter assumes the Postgres database/user/password is transiter/transiter/transiter.
If you have Docker installed,
    you can easily spin up the right kind of Postgres instance
    by running the following command:

```
docker run \
    -e POSTGRES_USER=transiter -e POSTGRES_PASSWORD=transiter -e POSTGRES_DB=transiter \
    -p 0.0.0.0:5432:5432 \
    postgis/postgis:14-3.4
```

You can also use a system-provided Postgres (e.g. `apt install postgresql`).
Most system-provided Postgres installations include PostGIS,
  as do most managed Postgres offerings by the main Cloud providers.


## Install and launch Transiter

After setting up Postgres, the next step is to start the Transiter server.
The Transiter server is the backend web service that does all the work of subscribing to transit data feeds,
  updating the data in Postgres,
  and providing data through the HTTP API.
A full production deployment of Transiter consists simply of Postgres and the Transiter server.
Later we will also learn about Transiter client commands,
  which are used to perform one-off administrative tasks on the server like installing the NYC subway.

First you need to install Transiter.
Transiter is distributed both as a single standalone binary or a Docker image.
There are few ways to install it:

1. Download a prebuilt binary from the [the GitHub releases page](https://github.com/jamespfennell/transiter/releases).

2. If you have Go installed, checkout the Transiter repo and simply run `go install .` in the repo's root.

3. Use the Transiter Docker image.
    To do this, replace all invocations of `transiter` below
    with `docker run --network=host jamespfennell/transiter:latest`.
    (It's possible and recommended to run the Docker image without
      using `--network=host`, but for now it's a convenient shortcut.
      See the [deployment page](deployment.md) for best practices on running Transiter with Docker.)

After installation, the Transiter _server_ is launched using:

```
transiter server --log-level debug
```

Depending on your Postgres setup,
  you may need to provide a custom Postgres connection config.
For example, you may be using a different username or password.
You can use the `-p` or `--postgres-connection-string` flag to provide the connection config:

```
transiter server -p postgresql://$USER:$PASSWORD@localhost:5432/$DATABASE_NAME
```

By default Transiter exports a few APIs on different ports.
The primary "public" HTTP API is exported on port 8000.
When the server is launched,
  you can navigate to `localhost:8080` in your web browser (or use `curl`) to the Transiter landing page:

```json
{
  "transiter": {
    "version": "1.0.0",
    "href": "https://github.com/jamespfennell/transiter"
  },
  "systems": {
    "count": "0"
  }
}
```

As you can see, there are no (transit) systems installed, and the next step is to install one!


## Install a transit system

Each deployment of Transiter can contain multiple _transit systems_ like the NYC subway.
A transit system is installed by providing Transiter with a YAML config file.
This config file
    contains basic metadata about the system (like its name) and
    the URLs of its GTFS data feeds.

The Transiter project maintains a [standard collection of transit systems](https://github.com/jamespfennell/transiter/tree/master/systems).
If the system you're interested in is already there, you can install it simply by providing Transiter with the
  system's ID.
For example, to install the San Francisco BART:

```
transiter install us-ca-bart
```

The command will take a few seconds to complete;
    most of the time is spent loading the BART's schedule into the database.
After it finishes, the Transiter landing page will show 1 system installed:

```json
{
  "transiter": {
    "version": "1.0.0",
    "href": "https://github.com/jamespfennell/transiter"
  },
  "systems": {
    "count": "1"
  }
}
```

The system can be found at `http://localhost:8080/systems/us-ca-bart`:

```json
{
  "id": "us-ca-bart",
  "resource": null,
  "name": "Bay Area Rapid Transit",
  "status": "ACTIVE",
  "agencies": {
    "count": "1"
  },
  "feeds": {
    "count": "3"
  },
  "routes": {
    "count": "14"
  },
  "stops": {
    "count": "186"
  },
  "transfers": {
    "count": "0"
  }
}
```

??? info "Installing a transit system from a file"
    If a system you're interested in is not in the Transiter repo,
    you can write a [transit system config file following this guide](systems.md),
    and then install the system by running `transiter install --file path/to/my-system.md`.
    The system will be given the ID `my-system`.

??? info "Customizing the system ID"
    By default the transit system ID is determined from the YAML file name.
    You can customize it by passing the flag `--id custom-id`.
    With this mechanism you can even install the same transit system multiple
    times under different IDs.


## Explore route data

Let's explore the data about routes that Transiter exposes.
All of the routes can be listed at `http://localhost:8080/systems/us-ca-bart/routes`.
We'll focus on a specific route, the *Berryessa/North San José–Richmond line* or *Orange Line* 
([Wikipedia page](https://en.wikipedia.org/wiki/Berryessa/North_San_Jos%C3%A9%E2%80%93Richmond_line)).
The route ID for this system is `3`, so we can find it by navigating to,

```text
http://localhost:8080/systems/us-ca-bart/routes/3
```

The API reference contains a [typed description of the route resource](api/public_resources.md#route)
  that is returned from this endpoint.
The start of response will look like this:

```json
{
  "id": "3",
  "resource": null,
  "system": null,
  "shortName": "Orange-N",
  "longName": "Berryessa/North San Jose to Richmond",
  "color": "FF9933",
  "textColor": "000000",
  "url": "https://www.bart.gov/schedules/bylineresults?route=3",
  "continuousPickup": "NOT_ALLOWED",
  "continuousDropOff": "NOT_ALLOWED",
  "type": "SUBWAY",
  "agency": {
    // pointer to the agency that runs BART
  },
  "alerts": [],
  "estimatedHeadway": 1198,
  "serviceMaps": [
    // service maps, discussed below
  ]
}
```

Most of the basic data here, such as [the color FF9933](https://www.color-hex.com/color/ff9933),
is taken from the GTFS Static feed.
The *alerts* are taken from the GTFS Realtime feed.
Depending on the current state of the system, this may be empty.
The *estimated headway* is calculated by Transiter.
It is the current average time between realtime trips on this route.
If there is insufficient data to estimate the headway, it will be `null`.

Arguably the most useful data here, though, are the *service maps*.


### Service maps

When transit consumers think of a route, they often think of the list of stops the route usually calls at.
In our example above, "the Orange Line goes from Richmond to San José."
Even though it's so central to how people think about routes, 
    GTFS does not directly give this kind of information.
However, Transiter has a system for automatically 
    generating such lists of stops using the timetable and realtime data in the GTFS feeds.
They're called *service maps* in Transiter.

Each route can have multiple service maps.
In the BART example there are three maps presented in the routes endpoint:

```json
{
  "serviceMaps": [
    {
      "configId": "alltimes",
      "stops": [
        {
          "id": "place_RICH",
          "name": "Richmond"
          // other fields
        },
        {
          "id": "place_DELN",
          "name": "El Cerrito Del Norte"
          // other fields
        },
        // intermediate stops
        {
          "id": "place_BERY",
          "name": "Berryessa / North San Jose"
          // other fields
        }
      ]
    }
    // 2 other service maps: weekday and realtime
  ]
}
```

Transiter generates service maps from two sources:

1. The realtime trips in the GTFS Realtime feeds.
    The `realtime` service map was generated in this way.

1. The timetable in the GTFS Static feeds.
    Transiter can calculate the service maps using every trip in the timetable, like the `all-times` service map.
    Transiter can also calculate service maps for a subset of the timetable - for example, just using
        the weekend trips, or just using the weekday trips.
    (The weekday service map will make an appearance below.)

More information on configuring service maps can be found in the 
    [service maps section](systems.md#service-maps)
    of the transit system config documentation page.

## Explore stop data

Next let's look at some stops data.
All of the BART's stops can be listed at `http://localhost:8080/systems/us-ca-bart/stops`.
As in GTFS static, a "stop" refer to a few different physical entities
  such as a station, a platform within a station, or a specific entrance to a station.

Let's go straight to the Downtown Berkeley station, which has stop ID `place_DBRK`
    and URL `http://localhost:8080/systems/us-ca-bart/stops/place_DBRK`.
The API reference contains a [typed description of the stop resource](api/public_resources.md#stop).
This is the start of what comes back:

```json
{
  "id": "place_DBRK",
  "resource": null,
  "system": null,
  "name": "Downtown Berkeley",
  "latitude": 37.87011,
  "longitude": -122.268109,
  "type": "STATION",
  "childStops": [
    // child stops in the GTFS static stops hierarchy
  ],
  "serviceMaps": [
    {
      "configId": "weekday",
      "routes": [
        {
          "id": "3",
          "color": "FF9933"
          // other fields
        },
        {
          "id": "4",
          "color": "FF9933"
          // other fields
        }
      ]
    }
  ]
  "stopTimes" [
    // stop times, discussed below
  ]
}
```

The basic data at the start again comes directly from GTFS Static.

Next, we again see service maps!
In the route endpoint, the service maps returned the list of stops a route called at.
At the stop endpoint we see the inverse of this: the list of routes that a stop is included in.
Like for routes, this is important data that consumers associate with a station
    ("at Downtown Berkeley, I can get on the Orange Line").
This is not given explicitly in the GTFS Static feed,
    but Transiter calculates automatically.
There are three service maps, as in the routes endpoint.

### Stop times

Going further down we see *alerts* (as mentioned above) and *transfers*.
Probably the most important field in the stop response is the *stop times*.
These show the realtime arrivals for the station.
  
```json
{
  "stop_times": [
    {
      "arrival": {
        "time": "1713882155",
        "delay": 0,
        "uncertainty": 30
      },
      "departure": {
        "time": "1713882179",
        "delay": 0,
        "uncertainty": 30
      },
      "future": true,
      "stopSequence": 16,
      "stop": {
        "id": "DBRK",
        "name": "Downtown Berkeley"
        // other fields
      },
      "trip": {
        "id": "1509201",
        "resource": {
          "path": "systems/us-ca-bart/routes/3/trips/1509201"
        },
        "route": {
          "id": "3",
          "color": "FF9933"
          // other fields
        },
        "destination": {
          "id": "DELN",
          "name": "El Cerrito Del Norte"
          // other fields
        },
        "directionId": false
      }
    }
    // more stop times
  ]
}
```

The response shows the arrival and departure times, as well as details
    on the associated trip, the associated vehicle (if defined in the feed),
    the route of trip,
    and the last stop the trip will make.


## Search for stops by location

So far we have navigated though Transiter's data using the resource hierarchy.

Another way to find stations is to perform a geographic search.
Suppose we're at [Union Square in San Francisco](https://en.wikipedia.org/wiki/Union_Square%2C_San_Francisco)
    whose coordinates are latitude 37.788056 and longitude -122.4075.
    and we want to see what BART stations are nearby.
We can perform a geographical search in Transiter using Transiter's
  list stops endpoint and specifying a `DISTANCE` search mode:

```
http://localhost:8080/systems/us-ca-bart/stops?search_mode=DISTANCE&latitude=37.788056&longitude=-122.4075&max_distance=1&filter_by_type=true&type=STATION
```

The `max_distance` parameter uses kilometers.

This returns two stations, starting with Powell Street, which is closest to Union Square.
The next closest station is Montgomery Street, which is 534 meters away.


## Where to go next?

- [Create a transit system config for a system you're interested in](systems.md).

- [Learn about deploying Transiter in production](deployment.md).

- [Consult the API reference to find other endpoints and data that Transiter exposes](api/public_resources.md).
