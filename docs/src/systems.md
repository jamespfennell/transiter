# Configuring transit systems

Transit systems - like the NYC subway or San Francisco BART -
  are added to Transiter by providing
  a YAML configuration file that contains information about the transit system.
You can find many examples of transit system configurations in
  [the `systems` subdirectory of the Transiter repository](https://github.com/jamespfennell/transiter/tree/master/systems).
If the system you're interested in is there, then you don't need to do anything!
From the root of the Transiter repository, you can install the system using:

```
transiter install $SYSTEM_ID
```

Otherwise, to add a transit system to Transiter you need to write a new YAML file.
At the very least, this file contains:

- The transit system's name.
- The URLs of its GTFS data feeds.

There are also some advanced configurations available, which are discussed below:

- Parameters (like API keys) that must be provided with system install requests.
- Custom definitions for the system's "service maps".

After writing a YAML file, the transit system is installed in the same way:

```
transiter install --file $PATH_TO_YAML_FILE
```

The system ID will be the name of the YAML file (e.g., `path/to/my-system.yaml`
will have ID `my-system`) but this can be overridden with the `--id` flag.

The schema for the YAML config is given by the
  [system config type](api/admin.md#systemconfig) in the API schema.
All of the `snake_case` field names in the proto are in `camelCase` in the YAML.


## Basic configuration

The following is basic example of a transit system configuration.
After presenting the full configuration, each section is described below.

```yaml
name: Transit system name

feeds:
  - id: gtfsstatic
    type: GTFS_STATIC
    url: https://www.transitsystem.com/feed_1

  - id: gtfsrealtime
    type: GTFS_REALTIME
    url: https://www.transitsystem.com/feed_2
    # Optional fields for the HTTP request. Generally these don't need to be set.
    headers:
    - X-Extra-Header: "header value"
    requestTimeoutMs: 4000
```


### Basic Transit system information

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
  - id: gtfsstatic
    # feed configuration...
```

The feed ID must be unique within the configuration file, and can't contain the `/` character.


### Feed type

The feed type tells Transiter what kind of feed this is.

```yaml
    type: GTFS_STATIC
```

There are currently 3 options:

- `GTFS_STATIC` a GTFS static feed.

- `GTFS_REALTIME` a GTFS realtime feed.

- `NYCT_TRIPS_CSV` this is a special type of feed and only relevant for the NYC subway.

The Transiter project is open to adding other types of feed,
  especially to support transit systems that don't provide data in the GTFS format.


### Feed URLs

The configuration for the feed includes with instructions
  for how to obtain it over the internet:

```yaml
    url: https://www.transitsystem.com/feed_2
    headers:
    - X-Extra-Header: "header value"
    requestTimeoutMs: 4000
```

Transiter will perform a `GET` request to the given URL with the specified headers
  and with the provided timeout.
If not specified:

- no additional headers are sent.

- a default timeout of 5 seconds is used.


### Advanced: scheduling policy

After a transit system is installed,
  Transiter periodically performs feed updates for all feeds in the system.
A feed update fetches new data from the feed URL and updates the data in Transiter accordingly.
By default Transiter uses the following schedule for feed updates:

- For GTFS realtime feeds, Transiter performs a feed update every 5 seconds.

- For GTFS static and other feeds,
    Transiter performs a feed update at around 3am in the timezone of the transit system.
    The timezone is read from the GTFS static data.

This behavior can be overridden by setting the `schedulingPolicy`
  field in the feed configuration.
For example, to update the feed every 20 seconds:

```yaml
feeds:
  - id: gtfsstatic
    # other fields...
    schedulingPolicy: PERIODIC
    periodicUpdatePeriodMs: 20000  # 20000 milliseconds = 20 seconds
```

To update the feed at 5pm every day in the US Eastern timezone:

```yaml
feeds:
  - id: gtfsstatic
    # other fields...
    schedulingPolicy: DAILY
    dailyUpdateTime: 17:00
    dailyUpdateTimezone: America/New_York
```

To stop automatic updates entirely:

```yaml
feeds:
  - id: gtfsstatic
    # other fields...
    schedulingPolicy: NONE
```

Note that feed updates can always be triggered manually
  by using the [feed update method in the admin API](api/admin.md#update-a-feed).


### Advanced: required for install

In the process of installing a transit system,
  Transiter by default performs feed updates for all static feeds in the system.
The motivation is that a transit system is not very useful without static data
  (like the list of all stations),
  and so to fully install a system the data must already be in place.
Transiter does not perform feed updates for realtime feeds during the install process.

This behavior can be overridden using the `requiredForInstall` field:

```yaml
feeds:
  - id: gtfsstatic
    # other fields...
    requiredForInstall: false

  - id: gtfsrealtime
    # other fields...
    requiredForInstall: true
```


### Advanced: GTFS realtime options

For GTFS realtime feeds,
  additional options can be provided the affect how the feed is parsed.
For example, Transiter supports GTFS realtime extensions for the NYC subway.
These additional options are set using the `gtfsRealtimeOptions` field
  and are described [in the API reference](api/admin.md#gtfsrealtimeoptions).


## User provided parameters 

Sometimes the transit system configuration
  needs to be personalized for each individual installation.
For example, if one of the feeds requires an API key,
  it's best to have that provided by the person installing the transit
  system rather than hard-coding a specific key into the configuration.
That way configurations can be safely shared without also sharing private keys.

To support these situations,
  Transiter has a way for system configuration files to accept parameters.
When installing a system using the CLI, the format is:

```
transiter install --arg name1=value1 --arg name2=value2 -f $TRANSIT_SYSTEM_ID $PATH_TO_YAML_FILE
```

When arguments are passed like this,
  Transiter interprets the configuration file as a Go template.
The arguments can be used in the YAML config using the `{{ .Args.name1 }}` syntax

The following is a simple example of providing an API key using arguments:
```yaml
    http:
      url: "https://www.transitsystem.com/feed_1?api_key={{ Args.api_key }}"
```

The [NYC Subway system configuration](https://github.com/jamespfennell/transiter/blob/master/systems/us-ny-subway.yaml)
 is an example of a real configuration that uses arguments.


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

- [New York City L route](https://demo.transiter.dev/systems/us-ny-subway/routes/L)
- [New York City Times Square station](https://demo.transiter.dev/systems/us-ny-subway/stops/127)


### Configuring service maps

Each route in a transit system can have multiple service maps.
The service maps desired are defined in the YAML configuration.
If no service maps are defined, the default service maps are used.

Here's an example of three service maps definitions; `any_time`, `weekday_day`, and `realtime`:

```yaml

serviceMaps:
  - id: alltimes
    source: STATIC
    threshold: 0.05
    
  - id: weekday_day
    source: STATIC
    staticOptions:
      days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
      startsLaterThan: 7
      endsEarlierThan: 19

  - id: realtime
    source: REALTIME
```

Let's step through the options for each one.

The `source` parameter can be either `STATIC`
(so the map is generated using the timetable data from the GTFS static feeds)
or `REALTIME` (so the map is generated using data from the GTFS realtime feeds).

The `threshold` parameter is a way of removing one-off trips that
may follow a non-standard list of stops.
A `threshold` of `0.05` means that, after collecting all of the trips
for a route, group them together based on the list of stops they call at,
and remove trips if their group accounts for less that 5% of the trips for the route.

The `staticOptions` field enables one to create maps based on
 certain portions of the timetable.
The `any_time` map contains no conditions: it's built using the full timetable.
However the `weekday_day` map contains three conditions: it only uses the timetable
corresponding to trips that:

- Run during the weekdays: `days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]`
- Start after 7am in the morning: `startsLaterThan: 7`
- End before 7pm in the evening: `endsEarlierThan: 19`.

