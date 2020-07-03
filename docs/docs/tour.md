# The Transiter Tour

The Tour is an introduction to Transiter - a getting started tutorial
    that will show you how to launch the software,
     configure it for transit systems you're interested in,
     and getting the data you want.


## Launch Transiter


To begin, we're going to launch Transiter.
The easiest way to do this is with Docker compose and the
    [standard Transiter compose config file](https://github.com/jamespfennell/transiter/blob/master/docker/docker-compose.yml).
Simply run,

    docker-compose up -f path/to/docker-compose.yml

It will take a minute for the images to download from Docker Hub and for the containers to be launched successfully.

When everything is launched, Transiter will be listening on port 8000.
If you navigate to `localhost:8000` in your web browser (or use `curl`), you will find the Transiter landing page,

```json
{
  "transiter": {
    "version": "0.4.5",
    "href": "https://github.com/jamespfennell/transiter",
    "docs": {
      "href": "https://demo.transiter.io/docs/"
    }
  },
  "systems": {
    "count": 0,
    "href": "https://demo.transiter.io/systems"
  }
}
```

As you can see, there are no (transit) systems installed, and the next step is to install one!

??? info "Running Transiter without Docker"
    It's possible to run Transiter on "bare metal" without Docker; 
    the [running Transiter](deployment/running-transiter.md) page details how.
    It's quite a bit more work though, so for getting started we recommend the Docker approach.

??? info "Building the Docker images locally"
    If you want to build the Docker images locally that's easy, too:
    just check out the [Transiter Git repository](https://github.com/jamespfennell/transiter)
    and in the root of repository run `make docker`.
   
## Install a system

Each deployment of Transiter can have multiple transit systems installed side-by-side.
A transit system is installed using a YAML configuration file that 
    contains basic metadata about the system (like its name),
    the URLs of the data feeds,
    and how to parse those data feeds (GTFS Static, GTFS Realtime, or a custom format).

For this tour, we're going to start by installing the BART system in San Francisco.
The YAML configuration file is stored in Github, you can [inspect it here](https://github.com/jamespfennell/transiter-sfbart/blob/master/Transiter-SF-BART-config.yaml).
The system in installed by sending a `PUT` HTTP request to the desired system ID.
In this case we'll install the system using ID `bart`,

```
curl -X PUT "localhost:8000/systems/bart?sync=true" \
     -F 'config_file=https://raw.githubusercontent.com/jamespfennell/transiter-sfbart/master/Transiter-SF-BART-config.yaml'
```

As you can see, we've provided a `config_file` form parameter that contains the URL of the config file.
It's also possible to provide the config as a file upload using the same `config_file` form parameter.

The request will take a few seconds to complete;
    most of the time is spent loading the BART's schedule into the database.
After it finishes, hit the Transiter landing page again to get,

```json
{
  "transiter": {
    "version": "0.4.5",
    "href": "https://github.com/jamespfennell/transiter",
    "docs": {
      "href": "https://demo.transiter.io/docs/"
    }
  },
  "systems": {
    "count": 1,
    "href": "http://localhost:8000/systems"
  }
}
```

It's installed! 
Next, navigate to the list systems endpoint.
The URL `http://localhost:8000/systems` is helpfully given in the JSON response.
We get,

```json
[
  {
    "id": "bart",
    "status": "ACTIVE",
    "name": "San Francisco BART",
    "href": "http://localhost:8000/systems/bart"
  }
]
```

Now navigating to the system itself, we get,


```json
{
  "id": "bart",
  "status": "ACTIVE",
  "name": "San Francisco BART",
  "agencies": {
    "count": 1,
    "href": "http://localhost:8000/systems/bart/agencies"
  },
  "feeds": {
    "count": 3,
    "href": "http://localhost:8000/systems/bart/feeds"
  },
  "routes": {
    "count": 14,
    "href": "http://localhost:8000/systems/bart/routes"
  },
  "stops": {
    "count": 177,
    "href": "http://localhost:8000/systems/bart/stops"
  },
  "transfers": {
    "count": 0,
    "href": "http://localhost:8000/systems/bart/transfers"
  }
}
```

This is an overview of the system, showing the number of various things like stops and routes,
as well as URLs for those.

## Explore route data

Let's dive into the routes data that Transiter exposes.
Navigating to the list routes endpoint (given above; `http://localhost:8000/systems/bart/routes`)
lists all the routes.
We'll focus on a specific route, the *Berryessa/North San José–Richmond line* or *Orange Line* 
([Wikipedia page](https://en.wikipedia.org/wiki/Berryessa/North_San_Jos%C3%A9%E2%80%93Richmond_line)).
The route ID for this system is `3`, so we can find it by navigating to,

```text
http://localhost:8000/systems/bart/routes/3
```

The start of response will look like this,

```json
{
  "id": "3",
  "color": "FF9933",
  "short_name": "OR-N",
  "long_name": "Berryessa/North San Jose to Richmond",
  "description": "",
  "url": "http://www.bart.gov/schedules/bylineresults?route=3",
  "type": "SUBWAY",
  "periodicity": 7.5,
  "agency": null,
  "alerts": [],
  "service_maps": // service map definitions in here
}
```

Most of the basic data here, such as [the color FF9933](https://www.color-hex.com/color/ff9933),
is taken from the GTFS Static feed.
The *alerts* are taken from the GTFS Realtime feed.
Depending on the current state of the system when you take the tour, this may be empty.
The *periodicity* is calculated by Transiter.
It is the current average time between realtime trips on this route.
If there is insufficient data to calculate the periodicity, it will be `null`.

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
In the BART example there are two maps presented in the routes endpoint: `all-times` and `realtime`:

```json
  "service_maps": [
    {
      "group_id": "all-times",
      "stops": [
        {
          "id": "place_RICH",
          "name": "Richmond",
          "href": "http://localhost:8000/systems/bart/stops/place_RICH"
        },
        {
          "id": "place_DELN",
          "name": "El Cerrito Del Norte",
          "href": "http://localhost:8000/systems/bart/stops/place_DELN"
        },
        // More stops ...
        {
          "id": "place_BERY",
          "name": "Berryessa",
          "href": "http://localhost:8000/systems/bart/stops/place_BERY"
        }
      ]
    },
    {
      "group_id": "realtime",
      "stops": [
        // List of stops ...
      ]
    }
  ]
```

Transiter enables generating service maps from two sources:

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

Having looked at routes, let's look at some stops data.
The endpoint for the BART transit system (`http://localhost:8000/systems/bart`)
tells us where the find the list of all stops (`http://localhost:8000/systems/bart/stops`).
Let's go straight to the Downtown Berkeley station, which has stop ID `place_DBRK`
    and URL `http://localhost:8000/systems/bart/stops/place_DBRK` 
    (both the ID and the URL can be found in the Orange Line's service map).
This is the start of what comes back:

```json
{
  "id": "place_DBRK",
  "name": "Downtown Berkeley",
  "longitude": "-122.268109",
  "latitude": "37.870110",
  "url": "",
  "service_maps": [
    {
      "group_id": "weekday",
      "routes": [
        {
          "id": "3",
          "color": "FF9933",
          "href": "http://localhost:8000/systems/bart/routes/3"
        },
        {
          "id": "4",
          "color": "FF9933",
          "href": "http://localhost:8000/systems/bart/routes/4"
        },
        {
          "id": "7",
          "color": "FF0000",
          "href": "http://localhost:8000/systems/bart/routes/7"
        },
        {
          "id": "8",
          "color": "FF0000",
          "href": "http://localhost:8000/systems/bart/routes/8"
        }
      ]
    }
  // more data
  ]
}
```

The basic data at the start again comes directly from GTFS Static.

Next, we again see service maps!
In the route endpoint, the service maps returned the list of stops a route called at.
At the stop endpoint we see the inverse of this: the list of routes that a stop is included in.
Like for routes, this is important data that consumers associate with a station
    ("at Downtown Berkeley, I can get on the Orange Line"),
    which is not given explicitly in the GTFS Static feed,
    and which Transiter calculates automatically.
The two service maps shown are `weekday`, which is built using the weekday schedule, and `realtime`.

Going further down we see *alerts* (as mentioned above) and *transfers* (will be mentioned below).
Probably the most important data at the stop however is the *stop times*:
    these show the realtime arrivals for the station.
```json
{
  // ...
  "stop_times": [
    {
      "arrival": {
        "time": 1593271377.0,
        "delay": 0,
        "uncertainty": 30
      },
      "departure": {
        "time": 1593271401.0,
        "delay": 0,
        "uncertainty": 30
      },
      "track": null,
      "future": true,
      "stop_sequence": 12,
      "direction": null,
      "trip": {
        "id": "2570751",
        "direction_id": false,
        "started_at": null,
        "updated_at": null,
        "delay": null,
        "vehicle": null,
        "route": {
          "id": "3",
          "color": "FF9933",
          "href": "http://localhost:8000/systems/bart/routes/3"
        },
        "last_stop": {
          "id": "DELN",
          "name": "El Cerrito Del Norte",
          "href": "http://localhost:8000/systems/bart/stops/DELN"
        },
        "href": "http://localhost:8000/systems/bart/routes/3/trips/2570751"
      }
    }
  ]
}
```

The response shows the arrival and departure times, as well as details
    on the associated trip, the associated vehicle (if defined in the feed),
    the route of trip,
    and the last stop the trip will make.


## Search for stops by location

So far we have navigated though Transiter's data using the links in each endpoint,
    starting from the system, to a route, to a stop.
Apps built on top of Transiter (like [realtimerail.nyc](https://www.realtimerail.nyc)) often follow this pattern.

Another way to find stops is to search for them by location,
    and Transiter supports this too.
Suppose we're at [Union Square in San Francisco](https://en.wikipedia.org/wiki/Union_Square%2C_San_Francisco)
    whose coordinates are latitude 37.788056 and longitude -122.4075.
    and we want to see what BART stations are nearby.
We can perform a geographical search in Transiter by sending a `POST` requqsts to the stops endpoint.
Using `curl`,

```
curl -X POST "http://localhost:8000/systems/bart/stops?latitude=37.788056&longitude=-122.4075"
```

This returns two stations, starting with Powell Street, which is closest to Union Square.
Its distance is returned as 383 meters.
The next closest station is Montgomery Street, which is 534 meters away.

```json

[
  {
    "id": "place_POWL",
    "name": "Powell Street",
    "distance": 383,
    "service_maps": [
      // ...
    ],
    "href": "http://localhost:8000/systems/bart/stops/place_POWL"
  },
  {
    "id": "place_MONT",
    "name": "Montgomery Street",
    "distance": 534,
    "service_maps": [
      // ...
    ],
    "href": "http://localhost:8000/systems/bart/stops/place_MONT"
  }
]
```

It's possible to search for more stops by passing a distance URL parameter to the search.

## Add inter-system transfers

Transiter supports installing multiple transit system side-by-side.
In many cases, these transit systems have connections between them,
    though this is not described in the single-system GTFS feeds.
Transiter provides a feature to create these inter-system transfers 
    by searching for stations in multiple systems that are geographically close to each other.
We'll demo this by showing to crate inter-system transfers between the BART and Caltrain.


First, put the following system config for the Caltrain in a file `caltrain.yaml` in your current working directory:
```yaml
name: Caltrain

feeds:
  GTFS-Static:
    http:
      url: http://data.trilliumtransit.com/gtfs/caltrain-ca-us/caltrain-ca-us.zip
    parser:
      built_in: GTFS_STATIC
``` 

Then install the Caltrain system:

```
curl -X PUT "localhost:8000/systems/caltrain?sync=true"  -F 'config_file=@caltrain.yaml'
```

Next, we'll preview what transfers we can create using geographic proximity.
The following command searches for BART and Caltrain stations that are within 200 meters of each other:
```
curl -X POST "http://localhost:8000/admin/transfers-config/preview?system_id=bart&system_id=caltrain&distance=200"
```

The response contains, essentially, a single match:
    the [Milbrae station](https://en.wikipedia.org/wiki/Millbrae_station) on the San Francisco peninsula.
Searching for transit connections between Caltrain and BART reveals that 
[this is the only official transfer](https://www.caltrain.com/riderinfo/connections.html).

??? question "Why does the Milbrae transfer appear four times in the result?"
    Like GTFS Static transfers, the inter-system transfers created by Transiter are uni-directional,
        with a specific *from* station and a specific *to* station.
    A bi-directional transfer is represented by two uni-directional transfers.
    This accounts for why Milbrae appears at least twice in the result.
    
    In addition, the Caltrain GTFS Static feed
    contains a separate station for the northbound (id=`70061`) and southbound directions (id=`70062`)
    at Milbrae and gives no indication that these two stations are actually one.
    Transiter then creates two uni-directional transfers for the BART station and the northbound Caltrain station,
    and another two for the BART station and the southbound Caltrain station.
    This gives four results in all.
    
    The Caltrain GTFS Static feed having two disconnected stops for one station
    is representive of the low-quality of many GTFS feeds provided by transit agencies.
    Transiter tries in many cases to account for low-quality data, but does not handle all cases.


It's possible to widen the scope of search by increasing the distance parameter.
If the distance is increased to one kilometer another results appears:
    a connection between the San Bruno BART and the San Bruno Caltrain:
    
```
curl -X POST "http://localhost:8000/admin/transfers-config/preview?system_id=bart&system_id=caltrain&distance=1000"
```

These stations are within walking distance of each other, but are not official connections.

Having previewed the result of the search, Transiter can now be instructed to create
    the transfers:

```
curl -X POST "http://localhost:8000/admin/transfers-config?system_id=bart&system_id=caltrain&distance=200"
```

Navigating to the Milbrae BART station endpoint (`http://localhost:8000/systems/bart/stops/place_MLBR`),
 the transfers will appear in the response,

```json
{
  // ...
  "transfers": [
    {
      "from_stop": {
        "id": "place_MLBR",
        "name": "Millbrae",
        "href": "http://localhost:8000/systems/bart/stops/place_MLBR"
      },
      "to_stop": {
        "id": "70061",
        "name": "Millbrae Caltrain",
        "system": {
          "id": "caltrain",
          "status": "ACTIVE",
          "name": "Caltrain",
          "href": "http://localhost:8000/systems/caltrain"
        },
      }
      // ...
    }
    // ...
  ]
  // ...
}
```

Because the Caltrain transfer is an inter-system transfer,
    its system is included in the response.
    
Full documentation for the inter-system transfers feature can be found in the
    [relevant API page](api/inter-system-transfers-management.md).
    
   
## Where to go next?


- Create a transit system config for a system you're interested in.

- Consult the API reference to find other endpoints and data that Transiter exposes.

- Learn about handling non-GTFS or extended-GTFS feeds.