# Configuring transit systems


Transit systems are added to Transiter using
a YAML configuration file.
The configuration file can be plain, or it can be a
 [Jinja template](https://jinja.palletsprojects.com/en/2.11.x/).
It contains information such as:

- The transit system's name.
- The URLs of its data feeds and instructions on how to parse the feeds.
- Definitions of "service maps" for the system.

The transit system is installed by sending the YAML
configuration file to the [system install endpoint](api/index.md#install-a-system).


## Basic configuration

The following is basic example of a transit system configuration.
After presenting the full configuration, each section is described below.

```yaml
name: Transit System Name
preferred_id: transit-system-id
timezone: America/New York

feeds:
  
  feed_one_id:
    http:
      url: https://www.transitsystem.com/feed_1
      headers:
      - X-Extra-Header: "header value"

    parser:
      built_in: "GTFS_STATIC" 

    auto_update:
      enabled: "true"
      period: "15 seconds"
  
     # If not specified, required_for_install defaults to false.
     # required_for_install: "false" 

  feed_two_id:
    http:
      url: https://www.transitsystem.com/feed_2

    parser:
      custom: "module:function"  

    # If not specified, auto-update is not enabled.
    # auto_update:
    #   enabled: "false"

    required_for_install: "true" 
```

### Basic Transit system information

The config begins with the Transit system name and an optional preferred ID:
```yaml
name: Transit System Name
preferred_id: transit-system-id
timezone: America/New York
```
The name can any string.
The preferred ID can be any valid system ID, and should be the "default" ID for the system.

### Feeds

Next, the config describes the *feeds* for the system.
This is the most important part of the configuration.

```yaml
feeds:
  
  feed_one_id:
    # feed configuration...
```

The feed ID can be any string you like, the only constraint is
that it be unique in this transit system. 

### Feed location

The configuration for the feed begins with instructions
on how to obtain it over the internet:

```yaml
    http:
      url: https://www.transitsystem.com/feed_1
      headers:
      - X-Extra-Header: "header value"
```

Transiter will perform a `GET` request to the given URL with the specified
headers. 
If not specified, no additional headers are sent.
If you require any additional configuration of the HTTP request,
for example sending a `POST` request instead, file an issue on the GitHub tracker
for this functionality to be added.

### Parser

After obtaining the feed, Transiter will parse it using the specified parser.
For the first feed in this example, the parser is one of two built-in parsers:
```yaml
    parser:
      built_in: "GTFS_STATIC"  
```
The two built-in parsers are:

- `GTFS_STATIC`
- `GTFS_REALTIME`

The second feed in this example uses a custom feed parser; i.e., a parser
provided by you, the administrator.
There is a [dedicated documentation page](feedparsers.md) on how to write custom feed parsers.
The syntax for a custom feed parser is:
```yaml
    parser:
      custom: "module:function"  
```

Here the custom feed parser is `function` defined in a given `module`.
Typically, the module will be defined using a package that is installed
in the Python environments Transiter is executing in; for example
`transiter_nycsubway.servicestatusxmlparser`.

Note that if the package and/or module is not available,
any feed updates will fail with reason `INVALID_PARSER`.

### Auto-update

Next, you can configure the feed to be auto-updating, meaning Transiter
will automatically perform feed updates with a desired frequency:
```yaml
    auto_update:
      enabled: "true"
      period: "15 seconds"
```
The period can be any human readable time interval
like "3 minutes", "five hours", "1 week", and so on.

In general, all feeds should be auto-updating.
For realtime feeds it's reasonable to update a few times every minute;
for static feeds, once a day usually makes sense.

### Required for install

Finally, you specify that a feed update takes place when
the system is being installed:
```yaml
     required_for_install: "true" 
```
The system install will fail if the feed update fails.

This is useful for GTFS static feeds, 
which often bring in basic information about the system 
(like the list of stops) which other realtime feeds rely on.

The feed update can fail for transient reasons (like a failed HTTP request),
and therefore to make system installs reliable you should only
set `required_for_install` for feeds that actually need it.

Note that `required_for_install` feed updates
take place sequentially, and in the order they are specified in the YAML
file.
This feature may be useful if one feed relies on data having been imported from
another feed.


## Adding user provided parameters 

Sometimes the transit system configuration
needs to be personalized for each individual installation.
For example, if one of the feeds requires an API key,
it's best to have that provided by the person installing the transit
system rather than hard-coding a specific key into the configuration.
That way configurations can be safely shared without also sharing private keys.

To support these situations, Transiter interprets every configuration
file as a Jinja template and processes the template before parsing the YAML.
Variables can be provided to the template using URL parameters in the
[system install endpoint](api/index.md#install-a-system).

The following is a simple example of providing an API key using Jinja:
```yaml
    http:
      url: "https://www.transitsystem.com/feed_1?api_key={{ user_api_key }}"
```
Here the user provided parameter is `api_key`.
The user installs the system by sending a `PUT` request to

    /systems/system_id?user_api_key=123456789

The [NYC Subway system configuration](https://github.com/jamespfennell/transiter-nycsubway) 
 is a good example
of a configuration using Jinja templates.

## Service maps

Service maps are a novel feature of Transiter that provide a rich 
connection between routes and stops that is missing in the standard GTFS static specification.

When people think of a route, like the
[L train in New York City](https://en.wikipedia.org/wiki/L_\(New_York_City_Subway_service\)),
they usually think about the list of stops the route calls at (8th Ave, 6th Ave, Union Sq...).
When people think of a stop, like 
[Pico station in Los Angeles](https://en.wikipedia.org/wiki/Pico_station),
they usually think of the routes available at that stop (the A and E lines).

The GTFS static specification does not contain this data *explicitly*.
Transiter service maps are built on the idea that this data is contained
in the static data *implicitly*.
Namely, if you have the complete timetable for a transit system, it is
possible to auto-generate the list of stops for each route by
merging together the paths
 taken by each trip in that route.
Once you have this list worked out for each route, for a given stop
you can then determine which routes call at it by finding the routes 
that contain the stop in the corresponding list.
 
Service maps implement this idea.
Moreover, service maps work not just for the complete timetable:
you can configure a service map for given "slices" of the timetable 
(for example the weekday day service), as well as for realtime data.

To see how service maps look in the HTTP API, check out
the `service_maps` data given in these endpoints:

- [New York City L route](https://demo.transiter.io/systems/nycsubway/routes/L)
- [New York City Times Square station](https://demo.transiter.io/systems/stops/127-725-902-A27-R16)


### Configuring service maps

Each route in a transit system can have multiple service maps.
The service maps desired are defined in the YAML configuration.
If no service maps are defined, the default service maps will be used.

Here's an example of three service maps definitions; `any_time`, `weekday_day`, and `realtime`:

```yaml
service_maps:

  any_time:
    source: SCHEDULE
    threshold: 0.05
    use_for_stops_in_route: true

  weekday_day:
    source: SCHEDULE
    conditions:
      weekday: true
      starts_later_than: 7
      ends_earlier_than: 19
    threshold: 0.1
    use_for_routes_at_stop: true

  realtime:
    source: REALTIME
    use_for_stops_in_route: true
    use_for_routes_at_stop: true
```

Let's step through the options for each one.

The `source` parameter can be either `SCHEDULE` 
(so the map is generated using the timetable data, for example from a GTFS static)
or `REALTIME` (so the map is generated using data, for example, from GTFS realtime feeds).

The `threshold` parameter is a way of removing one-off trips that
may follow a non-standard list of stops.
A `threshold` of `0.05` means that, after collecting all of the trips
for a route, group them together based on the list of stops they call at,
and remove trips if their group accounts for less that 5% of the trips for the route.

The `conditions` parameter enables one to create maps based on
 certain portions of the timetable.
The `any_time` map contains no conditions: it's built using the full timetable.
However the `weekday_day` map contains three conditions: it only uses the timetable
corresponding to trips that:

- Run during the weekday (`weekday: true`).
- Start after 7am in the morning (`starts_later_than: 7`).
- End before 7pm in the evening (`ends_earlier_than: 19`).

Finally, `use_for_routes_at_stop` being set to true 
indicates that the service map should be returned by the 
[stop endpoint](api/index.md#get-a-stop-in-a-system).
The parameter `use_for_stops_in_route` 
does the same for the [route endpoint](api/index.md#get-a-route-in-a-system).
