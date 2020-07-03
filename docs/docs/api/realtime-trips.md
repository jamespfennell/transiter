# Realtime trips


Endpoints for getting data on realtime trips in a route.

## List trips in a route

`GET /systems/<system_id>/routes/<route_id>/trips`


List all the realtime trips in a particular route.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system and route exist.
`404 NOT FOUND` | Returned if either the system or the route does not exist.

## Get a trip in a route

`GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`


Describe a trip in a route in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system, route and trip exist.
`404 NOT FOUND`     | Returned if the system, route or trip do not exist.
