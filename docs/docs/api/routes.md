# Routes


Endpoints for getting data on transit system routes.

## List routes in a system

`GET /systems/<system_id>/routes`


List all the routes in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

## Get a route in a system

`GET /systems/<system_id>/routes/<route_id>`


Describe a route in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and route exist.
`404 NOT FOUND`     | Returned if either the system or the route does not exist.
