# API reference


This page details the HTTP endpoints exposed by Transiter.
The API is largely RESTful.

Endpoints mostly return JSON data; exceptions are specifically noted.
In order to avoid stale documentation,
the structure of the JSON data returned by each endpoint
 is not described here, but can be inspected on the
[demo site](https://demo.transiter.io) or
by clicking any of the example links below.



## Endpoints quick reference

Operation                                           | API endpoint
----------------------------------------------------|--------------
[Entry point and about](#entry-point-and-about)     | `GET /`
[Documentation home page](#documentation-home-page) | `GET /docs`
**Transit systems**
[List all systems](#list-all-systems)               | `GET /systems`
[Get a system](#get-a-system)                       | `GET /systems/<system_id>`
[Install or update a system](#install-or-update-a-system)     | `PUT /systems/<system_id>`
[Delete a system](#delete-a-system)                 | `DELETE /systems/<system_id>`
[Configure system auto update](#configure-system-auto-update)   | `PUT /systems/<system_id>/auto-update`
**Feeds**   
[List feeds in a system](#list-feeds-in-a-system)   | `GET /systems/<system_id>/feeds`
[Get a feed](#get-a-feed-in-a-system)               | `GET /systems/<system_id>/feeds/<feed_id>`
[Perform a feed update](#perform-a-feed-update)     | `POST /systems/<system_id>/feeds/<feed_id>`
[Perform a feed flush](#perform-a-feed-flush)       | `POST /systems/<system_id>/feeds/<feed_id>/flush`
[List updates in a feed](#list-updates-for-a-feed)  | `GET /systems/<system_id>/feeds/<feed_id>/updates`
**Stops**
[List stops in a system](#list-stops-in-a-system)   | `GET /systems/<system_id>/stops`
[Get a stop](#get-a-stop-in-a-system)               | `GET /systems/<system_id>/stops/<stop_id>`
[Search for stops in a system based on location](#search-stops-in-a-system)      | `POST /systems/<system_id>/stops`
[Search for stops in all systems based on location](#search-stops-in-all-systems)               | `POST /stops`
**Routes**
[List routes in a system](#list-routes-in-a-system) | `GET /systems/<system_id>/routes`
[Get a route](#get-a-route-in-a-system)             | `GET /systems/<system_id>/routes/<route_id>`
[List trips in a route](#list-trips-in-a-route)     | `GET /systems/<system_id>/routes/<route_id>/trips`
[Get a trip](#get-a-trip-in-a-route)                | `GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`
**Admin**
[Transiter health status](#transiter-health-status) | `GET /admin/health`
[List scheduler tasks](#list-scheduler-tasks)       | `GET /admin/scheduler`
[Refresh scheduler tasks](#refresh-scheduler-tasks) | `POST /admin/scheduler`
[Upgrade database](#upgrade-database)               | `POST /admin/upgrade`

## Basic endpoints

### Entry point and about

`GET /`

This endpoint serves as an entry point to the API.
It also provides some basic "about" information: the Transiter version, a URL for the documentation,
and the number of transit systems installed.

Return code | Description
------------|-------------
`200 OK` | This code is always returned. 

### Documentation home page

`GET /docs`

If enabled and configured correctly, this endpoint returns the home page of the HTML documentation.
Additional pages, such as this one, can be accessed by navigating the documentation.

For information on enabling and configuring the documentation, see the [deployment guide](deployment.md).

Return code | Description
------------|-------------
`200 OK` | Returned if the documentation is enabled and setup correctly.
`404 NOT FOUND` | Returned if the documentation is disabled.
`503 SERVICE UNAVAILABLE` | Returned if the documentation is enabled, but Transiter detects that it is not setup correctly. 


## Transit system endpoints

### List all systems 

`GET /systems` 
[(example)](https://demo.transiter.io/systems)

List all transit systems that are installed 
in this Transiter instance.

Return code | Description
------------|-------------
`200 OK` | This code is always returned. The response is a list of dictionaries, one for for each system.

### Get a system

`GET /systems/<system_id>`
[(example)](https://demo.transiter.io/systems/nycsubway)

Get a system by its ID.

Return code | Description
------------|-------------
`200 OK` | Returned if the system with this ID exists. The response contains data about the system and links to contained entities.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

### Install or update a system 

`PUT /systems/<system_id>`

`PUT /systems/<system_id>?sync=true`

This endpoint is used to install or update transit systems. 
Installs can be performed asynchronously (recommended)
or synchronously (using `sync=true`; not recommended); 
see below for more information.

The endpoint accepts `multipart/form-data` requests.
There is a single required parameter, `config_file`, which 
specifies the YAML configuration file for the Transit system.
(There is a [dedicated documentation page](systems.md) concerned with creating transit system configuration files.)
The parameter can either be:

- A file upload of the configuration file, or
- A text string, which will be interpreted as a URL pointing to the configuration file.

In addition, depending on the configuration file, the endpoint will also accept extra text form data parameters.
These additional parameters are used for things like API keys, which are different 
for each user installing the transit system. 
The configuration file will customize certain information using the parameters - 
    for example, it might include an API key as a GET parameter in a feed URL.
If you are installing a system using a YAML configuration provided by someone else, you
 should be advised of which additional parameters are needed.
If you attempt to install a system without the required parameters, the install will fail and 
the response will detail which parameters you're missing.
 
#### Async versus sync

Often the install process is long because it often involves performing
large feed updates
of static feeds - for example, in the case of the New York City Subway,
an install takes close to two minutes.
If you perform a synchronous install, the install request is liable
to timeout - for example, Gunicorn by default terminates HTTP
requests that take over 60 seconds.
For this reason you should generally install asynchronously.

After triggering the install asynchronously, you can track its
progress by hitting the `GET` system endpoint repeatedly.

Synchronous installs are supported and useful when writing new 
transit system configs, in which case getting feedback from a single request
is quicker.


Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system already exists, in which case this is a no-op.
`201 CREATED`       | For synchronous installs, returned if the transit system was successfully installed.
`202 ACCEPTED`      | For asynchronous installs, returned if the install is successfully triggered.
`400 BAD REQUEST`   | Returned if the YAML configuration file cannot be retrieved. For synchronous installs, this code is also returned if there is any kind of install error.


### Delete a system 

`DELETE /systems/<system_id>`

`DELETE /systems/<system_id>?sync=true`

Delete a transit system.

You should almost always use the asynchronous version of this endpoint.
It works by changing the system ID to be a new "random" ID, and then performs
the delete asynchronously. 
This means that at soon as the asynchronous request ends (within a few milliseconds)
 the system ID is available. 
 
The actual delete takes about one minute for the NYC subway system.

Return code         | Description
--------------------|-------------
`202 ACCEPTED`      | For asynchronous deletes, returned if the delete is successfully triggered.
`204 NO CONTENT`    | For synchronous deletes, returned if the system was successfully deleted. 
`404 NOT FOUND`     | Returned if the system does not exist.


### Configure system auto-update

`PUT /systems/<system_id>/auto-update`

Configure whether auto-update is enabled for
 auto-updatable feeds in a system.

The endpoint takes a single form parameter `enabled`
which can either be `true` or `false` (case insensitive).

Return code         | Description
--------------------|-------------
`204 NO CONTENT`    | The configuration was applied successfully.
`400 BAD REQUEST`   | Returned if the form parameter is not provided or is invalied.
`404 NOT FOUND`     | Returned if the system does not exist.


## Feed endpoints

### List feeds in a system

`GET /systems/<system_id>/feeds`

List all the feeds in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists. 
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

### Get a feed in a system

`GET /systems/<system_id>/feeds/<feed_id>`

Describe a feed in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and feed exist.
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

### Perform a feed update

`POST /systems/<system_id>/feeds/<feed_id>`

`POST /systems/<system_id>/feeds/<feed_id>?sync=true`

Perform a feed update of the given feed. 
The response is a description of the feed update.

This endpoint is provided for one-off feed updates and development work.
In general feed updates should instead be scheduled periodically using the transit system configuration;
see the [transit system documentation](systems.md) for more information.

Return code         | Description
--------------------|-------------
`201 CREATED`       | Returned if the system and feed exist, in which case the update is _scheduled_ (and executed in the same thread, if sync).
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.


### Perform a feed flush

`POST /systems/<system_id>/feeds/<feed_id>/flush`

`POST /systems/<system_id>/feeds/<feed_id>/flush?sync=true`

The feed flush operation removes all entities from Transiter
that were added through updates for the given feed.
The operation is useful for removing stale data from the database.

Return code         | Description
--------------------|-------------
`201 CREATED`       | Returned if the system and feed exist, in which case the flush is _scheduled_ (and executed in the same thread, if sync).
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.


### List updates for a feed

`GET /systems/<system_id>/feeds/<feed_id>/updates`

List the most recent updates for a feed.
Up to one hundred updates will be listed.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and feed exist.
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

## Stop endpoints


### List stops in a system

`GET /systems/<system_id>/stops`

List all the stops in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists. 
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

### Get a stop in a system

`GET /systems/<system_id>/stops/<stop_id>`

Describe a stop in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and stop exist.
`404 NOT FOUND`     | Returned if either the system or the stop does not exist.

### Search stops in a system

`POST /systems/<system_id>/stops`

Search for stops in a system based on their proximity to a geographic root location. 
This endpoint can be used, for example, to list stops near a user given the user's location.

It takes three URL parameters:

- `latitude` - the latitude of the root location (required).
- `longitude` - the longitude of the root location (required).
- `distance` - the maximum distance, in meters, away from the root location that stops can be. 
            This is optional and defaults to 1000 meters (i.e., 1 kilometer). 1 mile is about 1609 meters.
   
The result of this endpoint is a list of stops ordered by distance, starting with the stop 
closest to the root location.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system exists.
`404 NOT FOUND`     | Returned if no system with the provided ID is installed.


### Search stops in all systems

`POST /stops`

This endpoint is identical to the endpoint above, except instead of searching for stops within
a specific system it searches for stops within all the installed systems.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned in all cases.


## Route endpoints


### List routes in a system

`GET /systems/<system_id>/routes`

List all the routes in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists. 
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

### Get a route in a system

`GET /systems/<system_id>/routes/<route_id>`

Describe a route in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and route exist.
`404 NOT FOUND`     | Returned if either the system or the route does not exist.



### List trips in a route

`GET /systems/<system_id>/routes/<route_id>/trips`

List all the realtime trips in a particular route.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system and route exist.
`404 NOT FOUND` | Returned if either the system or the route does not exist.

### Get a trip in a route

`GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`

Describe a trip in a route in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system, route and trip exist.
`404 NOT FOUND`     | Returned if the system, route or trip do not exist.

## Administration endpoints

### Transiter health status

`GET /admin/health`

Return Transiter's health status.
This describes whether or not the scheduler and executor cluster are up.

### List scheduler tasks

`GET /admin/scheduler`

List all tasks that are currently being scheduled by the scheduler.

This contains the feed auto update tasks as well as the cron task that trims old feed updates.

### Refresh scheduler tasks

`POST /admin/scheduler`

When this endpoint is hit the scheduler inspects the database and ensures that the right tasks are being scheduled
and with the right periodicity, etc.
This process happens automatically when an event occurs that
potentially requires the tasks list to be changed, like a system install or delete.
This endpoint is designed for the case when an admin manually edits something in the database and
wants the scheduler to reflect that edit.

### Upgrade database

`POST /admin/upgrade`

Upgrades the Transiter database to the schema/version associated to
the Transiter version of the webservice.
This endpoint is used during Transiter updates: after first updating
the Python code (or Docker contains), this endpoint can be hit to
upgrade the database schema.
It has the same effect as the terminal command:

    transiterclt db upgrade

