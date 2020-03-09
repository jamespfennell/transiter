# Custom feed parsers

## Introduction

Transiter has built-in support for the GTFS static and GTFS realtime
feed formats, but also has an API for users to provide custom feed parsers
which enable Transiter to read data in arbitrary feed formats.
This API was developed because
transit agencies sometimes distribute data in alternative formats.
For example, New York City Transit distributes NYC Subway alerts data
in an ad-hoc XML format, rather than using GTFS realtime's alerts feature.


Conceptually, a feed parser takes binary data in a feed
(like the binary data in a GTFS realtime feed) and converts
it into a format Transiter can understand.
Concretely, a feed parser is a Python function that accepts
a single `binary_content` argument and outputs an iterator
containing objects that are subtypes of `transiter.models.UpdatableEntity`.
There are currently five subtypes of `UpdatableEntity`, and these determine
which kind of data you can import:

- `transiter.models.Route` - represents a transit route.
  Analogous to `routes.txt` in a GTFS static feed.
- `transiter.models.Stop` - represents a station.
  Analogous to `stops.txt` in a GTFS static feed.
- `transiter.models.ScheduledService` - this is an object that
  contains multiple objects of type `ScheduledTrip` and provides a mechanism for
  representing a portion of
  the timetable of a transit system.
- `transiter.models.Trip` - represents a realtime trip.
  Analogous to the trip and vehicle entities in a GTFS realtime feed.
- `transiter.models.Alert` - represents an alert or status update
  for an entity in a transit system.
  Analogous to the alert entity entity in a GTFS realtime feed.
- `transiter.models.DirectionRule` - represents a rule for 
    determining the direction (or headsign) of a trip at a stop.
    This is a Transiter-only entity that has no analog in the GTFS specs.


Full documentation on these entities and the data you can place in them
is given below in the reference section.

## An example feed parser

The feed parser API was designed so that the parsers themselves
could be simple.
Let's illustrate by way of example.
Suppose that we have a transit agency that distributes
alerts in CSV format, so that a version of the feed looks something like this:

```text
alert_id,alert_name,alert_text,route_affected
12345,Delays,Delays in southbound A service,A
```


A parser for this feed might look like this:

```python
import csv
import transiter

def parser(binary_content):
    lines = binary_content.decode("utf-8")
    csv_reader = csv.DictReader(lines)
    for row in csv_reader:
        alert = transiter.models.Alert()
        alert.id = row["alert_id"],
        alert.header = row["alert_name"]
        alert.description = row["alert_text"]
        alert.route_ids = [row["route_affects"]]
        yield alert
```

By providing just this code to Transiter, it
will be able to read feeds in this ad-hoc CSV format.


The custom feed parser for the NYC Subway's alerts
feed is a good production example of a Transiter custom feed parser.


## Registering your feed parser with Transiter

After writing a custom feed parser, you need to instruct
Transiter to use it for reading specific feeds.
First, you must place your feed parser in a Python package
and install that package in the Python environment that Transiter
is running in.
Then, in the system configuration YAML file for the transit system
you're working with, specify the custom parser:

```yaml
feeds:

  myfeed:
    http:
      url: 'http://www.transitagency.com/feed'  # the URL the feed is at
    parser:
      custom: 'mypackage.mymodule:parser'  # specifying the parser
```


Note that parsers are specified in the form
`package:function`.



## Working with GTFS realtime extensions

The GTFS realtime format supports extensions, which provide
a mechanism for transit agencies to provide additional data
in their realtime feeds.
The NYC Subway realtime feed is an example of a feed using a GTFS realtime extension.
These kinds of feeds can still be read using Transiter's built-in
GTFS realtime parser, but the data in the extension will
be silently ignored.

If you want to also work with the data in the extension,
Transiter has some tooling to help.
You need to provide two things:

1. A module for reading the GTFS realtime feed.
   This is typically the standard `google.transit.gtfs_realtime_pb2`
   module with some alteration made so that the protobuf extension
   can be read.

2. A post protobuf parsing function that accepts a JSON representation
   of the GTFS realtime document (with the extension data) and squashes
   the extension data onto the standard GTFS realtime attributes.

With these two ingredients, you
can use Transiter's GTFS realtime parsing factory to make
a custom parser:


```python
from transiter.services.update import gtfsrealtimeparser

parser = gtfsrealtimeparser.create_parser(
    gtfs_realtime_module,
    post_parsing_function
)
```


An example of this in practice is the NYC Subway's realtime parser.





## Reference

This reference provides information
on the entities that can be returned by a custom feed parser.

### Routes

The `transiter.models.Route` object
supports setting the following attributes:

- `id` - mandatory.
- `color`
- `short_name`
- `long_name`
- `description`
- `url`

### Stops

The `transiter.models.Stop` object
supports setting the following attributes:

- `id` - mandatory.
- `name`
- `longitude`
- `latitude`
- `is_station`
- `parent_stop` - a `Stop` object representing the parent stop.
  Unlike GTFS static, Transiter supports arbitrarily deep stop graphs.

### ScheduledServices (the timetable)

This object is used to communicate a portion of
the timetable of a transit system.

The `transiter.models.ScheduledService` object
supports setting the following attributes:

- `id` - mandatory.
- `monday` through `sunday` - booleans
  determining whether the service is in operation on the given day.
- `trips` - a list of `transiter.models.ScheduledTrip` objects
  representing the trips in the service.


The `transiter.models.ScheduledTrip` object
supports setting the following attributes:

- `id` - mandatory.
- `direction_id` - boolean discriminating between trips going in one
  direction (true) and in the opposite direction (false).
- `route_id` - ID of the route the trip is associated to.
- `stop_times_light` - a list of `transiter.models.ScheduledTripStopTimeLight`
  objects representing the stops and times in the trip.


The `transiter.models.ScheduledTripStopTimeLight` object
supports setting the following attributes:

- `stop_id` - ID of the stop for this stop time.
- `stop_sequence`
- `arrival_time` - a `datetime.datetime` object.
- `departure_time` - a `datetime.datetime` object.


### Trips

This object is used to communicate realtime data about
a current trip in a transit system.


The `transiter.models.Trip` object
supports setting the following attributes:

- `id` - mandatory.
- `route_id` - ID of the route corresponding to the trip.
- `direction_id` - boolean discriminating between trips going in one
  direction (true) and in the opposite direction (false).
- `current_status` - must be an element of the enum `transiter.models.Trip.TripStatus`.
- `current_stop_sequence`
- `start_time` - a `datetime.datetime` object.
- `last_update_time` - a `datetime.datetime` object.
- `stop_times` - a list of `transiter.models.TripStopTime`
  objects representing the stops and times in the trip.

The `transiter.models.ScheduledTripStopTimeLight` object
supports setting the following attributes:

- `future`
- `stop_id` - ID of the stop for this stop time.
- `stop_sequence`
- `arrival_time` - a `datetime.datetime` object.
- `departure_time` - a `datetime.datetime` object.
- `track`



### Alerts

The `transiter.models.Alert` object
supports setting the following attributes:

- `header`
- `description`
- `cause` - must be an element of the enum `transiter.models.Alert.Cause`.
- `effect` - must be an element of the enum `transiter.models.Alert.Effect`.
- `priority`
- `start_time` - a `datetime.datetime` object.
- `end_time` - a `datetime.datetime` object.
- `creation_time` - a `datetime.datetime` object.
- `route_ids` - a list IDs for the routes the alert is associated to.


### Direction rules

Direction rules are used to compensate for the lack of a per-stop
headsign field in the GTFS realtime spec.
The direction rules system is used to determine the direction
 of a trip at a given stop (for example, "uptown" versus "downtown").
Of all direction rules that match, the rule with the highest priority is used
for provide the direction.

The New York City Subway uses a [https://github.com/jamespfennell/transiter-nycsubway/blob/master/transiter_nycsubway/stationscsvparser.py](custom direction rules parser).

The `transiter.models.DirectionRule` object
supports setting the following attributes:

- `priority` - an integer, the priority of the rule. Lower integers are favored.
- `stop_id` - the stop this rule is for.
- `direction_id` - boolean corresponding to the trip's direction ID.
- `track` - the track.
- `name` - the name of the direction to be applied to trips matching this rule.

