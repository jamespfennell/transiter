# Feeds


Endpoints for getting information on feeds and for triggering feed updates.

## List feeds in a system

`GET /systems/<system_id>/feeds`


List all the feeds in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

## Get a feed in a system

`GET /systems/<system_id>/feeds/<feed_id>`


Describe a feed in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and feed exist.
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

## Perform a feed update

`POST /systems/<system_id>/feeds/<feed_id>`


Perform a feed update of the given feed.
The response is a description of the feed update.

This endpoint is provided for one-off feed updates and development work.
In general feed updates should instead be scheduled periodically using the transit system configuration;
see the [transit system documentation](systems.md) for more information.

Return code         | Description
--------------------|-------------
`201 CREATED`       | Returned if the system and feed exist, in which case the update is _scheduled_ (and executed in the same thread, if sync).
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

## Perform a feed flush

`POST /systems/<system_id>/feeds/<feed_id>/flush`


The feed flush operation removes all entities from Transiter
that were added through updates for the given feed.
The operation is useful for removing stale data from the database.

Return code         | Description
--------------------|-------------
`201 CREATED`       | Returned if the system and feed exist, in which case the flush is _scheduled_ (and executed in the same thread, if sync).
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

## List updates for a feed

`GET /systems/<system_id>/feeds/<feed_id>/updates`


List the most recent updates for a feed.
Up to one hundred updates will be listed.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and feed exist.
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.
