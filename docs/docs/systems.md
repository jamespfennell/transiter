# Configuring transit systems


Transit systems are added to Transiter using
a YAML configuration file.
This file contains information such as:

- The transit system's name,
- The internet location of its data feeds and instructions on how to parse them,
- Additional Python packages needed for the transit system.

The transit system is installed by sending the YAML
configuration file to the [system install endpoint](api.md#install-a-system).

## Basic configuration

The following is basic example of a transit system configuration.
After presenting the full configuration, each section is described below.

```yaml
name: Transit System Name

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

### Transit system name

The config begins with the Transit system name:
```yaml
name: Transit System Name
```
The name can any string.

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
This is useful for GTFS static feeds, 
which often bring in basic information about the system 
(like the list of stops) which other realtime feeds rely on.
If the feed update fails, the system install will fail.
Note the feed update can fail for transient reasons (like a failed HTTP request),
and therefore to make system installs reliable you should only
set `required_for_install` for feeds that actually need it.

Note that `required_for_install` feed updates
take sequentially, and in the order they are specified in the YAML
file.
This feature may be useful if one feed relies on data having been populated from
another feed.


## Adding user provided parameters 

Sometimes the transit system configuration
needs to be personalized for each individual installation.
For example, if one of the feeds requires an API key,
it's best to have that provided by the person installing the transit
system rather than hard-coding a specific key into the configuration.

To support these situations, Transiter 0.3 has some support for customizing
the configuration with user provided parameters. 
These parameters are provided by the person
installing the system using the [system install endpoint](api.md#install-a-system).


The parameters system in version 0.3 uses Python's `format` system.
When parsing the configuration, every value in the YAML file is
 passed through Python's `format` function with the user provided
 parameters as variable values.
This allows variables to be substituted.
For example:
```yaml
    http:
      url: "https://www.transitsystem.com/feed_1?api_key={api_key}"
```
Here the user provided parameter is `api_key`,
and during parsing the value provided by the user will be substituted in.

The [NYC Subway system configuration](https://github.com/jamespfennell/transiter-nycsubway) 
 is a good example
of a configuration using a user parameter.

**Note**: this ad-hoc system formatting will be replaced in Transiter 0.4
by a more robust and flexible system based on Jinja templates.

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
The observation that led to Transiter service maps is that this data is contained
in the static data *implicitly*.
Namely, if you have the complete timetable for a transit system, it should
be possible to auto-generate the list of stops for each route by
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

For each route in a transit system you can have multiple
service maps.
The service maps desired are defined in the YAML configuration.
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
[stop endpoint](api.md#get-a-stop-in-a-system).
The parameter `use_for_stops_in_route` 
does the same for the [route endpoint](api.md#get-a-route-in-a-system).
