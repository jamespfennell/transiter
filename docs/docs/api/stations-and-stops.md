# Stations and stops


Endpoints for getting data on stations and stops.

## List stops in a system

`GET /systems/<system_id>/stops`


List all the stops in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

## Search for stops

`POST /stops`


Search for stops in all systems based on their proximity to a geographic root location.
This endpoint can be used, for example, to list stops near a user given the user's location.

It takes three URL parameters:

- `latitude` - the latitude of the root location (required).
- `longitude` - the longitude of the root location (required).
- `distance` - the maximum distance, in meters, away from the root location that stops can be.
            This is optional and defaults to 1000 meters (i.e., 1 kilometer). 1 mile is about 1609 meters.

The result of this endpoint is a list of stops ordered by distance, starting with the stop
closest to the root location.

## Search for stops in a system

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

## Get a stop in a system

`GET /systems/<system_id>/stops/<stop_id>`


Describe a stop in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and stop exist.
`404 NOT FOUND`     | Returned if either the system or the stop does not exist.
