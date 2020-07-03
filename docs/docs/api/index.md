
# Endpoints list

Transiter's HTTP endpoints mostly return JSON data; exceptions are specifically noted.
In order to avoid stale documentation,
the structure of the JSON data returned by each endpoint
 is not described here, but can be inspected on the
[demo site](https://demo.transiter.io) or
by clicking any of the example links below.

!!! warning "Permissions levels"
    Every endpoint has an associated *permissions level* to enable access control.
    In production, you will likely *not* want to allow access to all endpoints - 
        for example, you will want to prohibit users from deleting systems.
    The [permissions documentation page](../deployment/permissions.md) describes
        the permissions system and how you can use it to deploy Transiter safely.

    If an endpoint does not describe a permissions level, then it does
    not impose any permissions restrictions.

Operation | API endpoint
----------|-------------
**entry-point-and-docs endpoints**
[HTTP API entry point](entry-point-and-docs.md#http-api-entry-point) | `GET /`
[Internal documentation](entry-point-and-docs.md#internal-documentation) | `GET /docs/<path:path>`
**systems endpoints**
[List all systems](systems.md#list-all-systems) | `GET /systems`
[Get a specific system](systems.md#get-a-specific-system) | `GET /systems/<system_id>`
[List all transfers in a system](systems.md#list-all-transfers-in-a-system) | `GET /systems/<system_id>/transfers`
[Install a system](systems.md#install-a-system) | `PUT /systems/<system_id>`
[Uninstall (delete) a system](systems.md#uninstall-(delete)-a-system) | `DELETE /systems/<system_id>`
[Configure system auto-update](systems.md#configure-system-auto-update) | `PUT /systems/<system_id>/auto-update`
**stations-and-stops endpoints**
[List stops in a system](stations-and-stops.md#list-stops-in-a-system) | `GET /systems/<system_id>/stops`
[Search for stops](stations-and-stops.md#search-for-stops) | `POST /stops`
[Search for stops in a system](stations-and-stops.md#search-for-stops-in-a-system) | `POST /systems/<system_id>/stops`
[Get a stop in a system](stations-and-stops.md#get-a-stop-in-a-system) | `GET /systems/<system_id>/stops/<stop_id>`
**routes endpoints**
[List routes in a system](routes.md#list-routes-in-a-system) | `GET /systems/<system_id>/routes`
[Get a route in a system](routes.md#get-a-route-in-a-system) | `GET /systems/<system_id>/routes/<route_id>`
**realtime-trips endpoints**
[List trips in a route](realtime-trips.md#list-trips-in-a-route) | `GET /systems/<system_id>/routes/<route_id>/trips`
[Get a trip in a route](realtime-trips.md#get-a-trip-in-a-route) | `GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`
**agencies endpoints**
[List agencies in a system](agencies.md#list-agencies-in-a-system) | `GET /systems/<system_id>/agencies`
[Get an agency in a system](agencies.md#get-an-agency-in-a-system) | `GET /systems/<system_id>/agencies/<agency_id>`
**feeds endpoints**
[List feeds in a system](feeds.md#list-feeds-in-a-system) | `GET /systems/<system_id>/feeds`
[Get a feed in a system](feeds.md#get-a-feed-in-a-system) | `GET /systems/<system_id>/feeds/<feed_id>`
[Perform a feed update](feeds.md#perform-a-feed-update) | `POST /systems/<system_id>/feeds/<feed_id>`
[Perform a feed flush](feeds.md#perform-a-feed-flush) | `POST /systems/<system_id>/feeds/<feed_id>/flush`
[List updates for a feed](feeds.md#list-updates-for-a-feed) | `GET /systems/<system_id>/feeds/<feed_id>/updates`
**inter-system-transfers-management endpoints**
[List all transfers configs](inter-system-transfers-management.md#list-all-transfers-configs) | `GET /admin/transfers-config`
[Preview a transfers config](inter-system-transfers-management.md#preview-a-transfers-config) | `POST /admin/transfers-config/preview`
[Create a transfers config](inter-system-transfers-management.md#create-a-transfers-config) | `POST /admin/transfers-config`
[Get a transfers config](inter-system-transfers-management.md#get-a-transfers-config) | `GET /admin/transfers-config/<int:config_id>`
[Update a transfers config](inter-system-transfers-management.md#update-a-transfers-config) | `PUT /admin/transfers-config/<int:config_id>`
[Delete a transfers config](inter-system-transfers-management.md#delete-a-transfers-config) | `DELETE /admin/transfers-config/<int:config_id>`
**admin endpoints**
[Transiter health status](admin.md#transiter-health-status) | `GET /admin/health`
[List scheduler tasks](admin.md#list-scheduler-tasks) | `GET /admin/scheduler`
[Refresh scheduler tasks](admin.md#refresh-scheduler-tasks) | `POST /admin/scheduler`
[Upgrade database](admin.md#upgrade-database) | `POST /admin/upgrade`
