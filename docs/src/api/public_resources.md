

# Public API resources

The public API is Transiter's main API and
is used to query transit data from Transiter.
It's a read-only API and designed to be reachable from the internet.

Transiter's other API is the private [admin API](admin.md) which is used to manage the Transiter deployment.

The public API is based on the following resource hierarchy:

```
System
|- Agency
|- Alert
|- Feed
|- Route
|   |- Trip
|- Shape
|- Stop
|- Transfer
|- Vehicle
```

For each resource there is a protobuf message type, a list endpoint, and a get endpoint.
In the HTTP API, the structure of the response is based on the protobuf message type.

The URLs in the HTTP API are determined by the resource hierarchy; thus:

- List all systems has URL `/systems`,
- Get system with ID `<system_id>` has URL `/systems/<system_id>`,
- List all routes in the system has URL `/systems/<system_id>/routes`,
- Get route has URL `/systems/<system_id>/routes/<route_id>`,

and so on.

The following table summarizes all of the resources and their types.
The right-most column describes the _source_ of the resource.
The public API is a read-only API so all of the resources come from somewhere else.

| Resource              | List endpoint                                       | Get endpoint                                    | Source               |
| --------------------- | --------------------------------------------------- | ----------------------------------------------- |----------------------|
| [Agency](#agency)     | [ListAgencies](public_endpoints.md#list-agencies)   | [GetAgency](public_endpoints.md#get-agency)     | GTFS static          |
| [Alert](#alert)       | [ListAlerts](public_endpoints.md#list-alerts)       | [GetAlert](public_endpoints.md#get-alert)       | GTFS realtime        |
| [Feed](#feed)         | [ListFeeds](public_endpoints.md#list-feeds)         | [GetFeed](public_endpoints.md#get-feed)         | System configuration |
| [Route](#route)       | [ListRoutes](public_endpoints.md#list-routes)       | [GetRoute](public_endpoints.md#get-route)       | GTFS static          |
| [Shape](#shape)       | [ListShapes](public_endpoints.md#list-shapes)       | [GetShape](public_endpoints.md#get-shape)       | GTFS static          |
| [Stop](#stop)         | [ListStops](public_endpoints.md#list-stops)         | [GetStop](public_endpoints.md#get-stop)         | GTFS static          |
| [System](#system)     | [ListSystems](public_endpoints.md#list-systems)     | [GetSystem](public_endpoints.md#get-system)     | System configuration |
| [Transfer](#transfer) | [ListTransfers](public_endpoints.md#list-transfers) | [GetTransfer](public_endpoints.md#get-transfer) | GTFS static          |
| [Trip](#trip)         | [ListTrips](public_endpoints.md#list-trips)         | [GetTrip](public_endpoints.md#get-trip)         | GTFS realtime        |
| [Vehicle](#vehicle)   | [ListVehicles](public_endpoints.md#list-vehicles)   | [GetVehicle](public_endpoints.md#get-vehicle)   | GTFS realtime        |

Many resources refer to other resources across the hierarchy.
For example, each route has an agency it is attached to.
Each stop has a list of service maps, and each service map contains a set of routes.
In these situations the resource message contains a _reference_ to the other resource.
The [Route](#route) message contains an agency reference, in the form of an [Agency.Reference](#agencyreference)
message.
These reference messages contain at least enough information to uniquely identify the resource.
However they also contain additional information that is considered generally useful.
For example, the [Stop.Reference](#stopreference) message contains the stop's name.
What counts as "considered generally" is obviously subjective and open to change.



## Agency

The Agency resource.

This resource corresponds to the [`agency.txt` table in the GTFS static
specification](https://gtfs.org/schedule/reference/#agencytxt).
Most of the fields in the resource come directly from the `agency.txt` table.
Transiter adds some additional related fields (routes, alerts).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the agency. This is the `agency_id` column in `agency.txt`.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the agency resource.
| system | [System.Reference](public_resources.md#systemreference) | System corresponding to this agency. This is the parent resource in Transiter's resource hierarchy.
| name | string | Name of the agency. This is the `agency_name` column in `agency.txt`.
| url | string | URL of the agency. This is the `agency_url` column in `agency.txt`.
| timezone | string | Timezone of the agency. This is the `agency_timezone` column in `agency.txt`.
| language | string | Language of the agency. This is the `agency_lang` column in `agency.txt`.
| phone | string | Phone number of the agency. This is the `agency_phone` column in `agency.txt`.
| fare_url | string | URL where tickets for the agency's services ban be bought. This is the `agency_fare_url` column in `agency.txt`.
| email | string | Email address of the agency. This is the `agency_email` column in `agency.txt`.
| routes | [Route.Reference](public_resources.md#routereference) | List of routes operating under this agency.<br /><br />These are determined using the `agency_id` column in `routes.txt`.
| alerts | [Alert.Reference](public_resources.md#alertreference) | List of active alerts for the agency.<br /><br />These are determined using the `informed_entity` field in the [GTFS realtime alerts message](https://gtfs.org/realtime/reference/#message-alert).






#### Agency.Reference

Reference type for the agency resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.
| system | [System.Reference](public_resources.md#systemreference) | Same as the parent message.
| name | string | Same as the parent message.









## Alert

The Alert resource.

This resource corresponds to the [alert message in the GTFS realtime
specification](https://gtfs.org/realtime/reference/#message-alert).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the alert. This corresponds to the [ID field in the feed entity message](https://gtfs.org/realtime/reference/#message-feedentity) corresponding to the alert.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the alert resource.
| system | [System.Reference](public_resources.md#systemreference) | System corresponding to this alert. This is the parent resource in Transiter's resource hierarchy.
| cause | [Alert.Cause](public_resources.md#alertcause) | Cause of the alert. This corresponds to the `cause` field in the realtime alert message.
| effect | [Alert.Effect](public_resources.md#alerteffect) | Effect of the alert. This corresponds to the `effect` field in the realtime alert message.
| current_active_period | [Alert.ActivePeriod](public_resources.md#alertactiveperiod) | The current active period, if the alert is currently active. If the alert is not active this is empty.
| all_active_periods | [Alert.ActivePeriod](public_resources.md#alertactiveperiod) | All active periods for this alert. Transiter guarantees that these active periods have no overlap.
| header | [Alert.Text](public_resources.md#alerttext) | Header of the alert, in zero or more languages. This corresponds to the `header_text` field in the realtime alert message.
| description | [Alert.Text](public_resources.md#alerttext) | Description of the alert, in zero or more languages. This corresponds to the `description_text` field in the realtime alert message.
| url | [Alert.Text](public_resources.md#alerttext) | URL for additional information about the alert, in zero or more languages. This corresponds to the `url` field in the realtime alert message.






#### Alert.ActivePeriod

The active period message describes a period when an alert is active.
It corresponds the the [time range message in the GTFS realtime
specification](https://gtfs.org/realtime/reference/#message-timerange).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| starts_at | int64 | Unix timestamp of the start time of the active period. If not set, the alert be interpreted as being always active up to the end time.
| ends_at | int64 | Unix timestamp of the end time of the active period. If not set, the alert be interpreted as being indefinitely active.






#### Alert.Cause

Cause is the same as the [cause enum in the GTFS realtime
specification](https://gtfs.org/realtime/reference/#enum-cause),
except `UNKNOWN_CAUSE` has value 0 instead of 1 to satisfy protobuf3 requirements.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN_CAUSE | 0 |  |
| OTHER_CAUSE | 2 |  |
| TECHNICAL_PROBLEM | 3 |  |
| STRIKE | 4 |  |
| DEMONSTRATION | 5 |  |
| ACCIDENT | 6 |  |
| HOLIDAY | 7 |  |
| WEATHER | 8 |  |
| MAINTENANCE | 9 |  |
| CONSTRUCTION | 10 |  |
| POLICE_ACTIVITY | 11 |  |
| MEDICAL_EMERGENCY | 12 |  |



#### Alert.Effect

Effect is the same as the [effect enum in the GTFS realtime
specification](https://gtfs.org/realtime/reference/#enum-effect),
except `UNKNOWN_EFFECT` has value 0 instead of 1 to satisfy protobuf3 requirements.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN_EFFECT | 0 |  |
| NO_SERVICE | 1 |  |
| REDUCED_SERVICE | 2 |  |
| SIGNIFICANT_DELAYS | 3 |  |
| DETOUR | 4 |  |
| ADDITIONAL_SERVICE | 5 |  |
| MODIFIED_SERVICE | 6 |  |
| OTHER_EFFECT | 7 |  |
| STOP_MOVED | 9 |  |
| NO_EFFECT | 10 |  |
| ACCESSIBILITY_ISSUE | 11 |  |



#### Alert.Reference

Reference type for the agency resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.
| system | [System.Reference](public_resources.md#systemreference) | Same as the parent message.
| cause | [Alert.Cause](public_resources.md#alertcause) | Same as the parent message.
| effect | [Alert.Effect](public_resources.md#alerteffect) | Same as the parent message.






#### Alert.Text

The text message describes an alert header/description/URL in a specified language.
It corresponds the the [translation message in the GTFS realtime
specification](https://gtfs.org/realtime/reference/#message-translation).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| text | string | Content of the text.
| language | string | Language of this text.









## ChildResources

Description of a collection of child resources for a resource.
This message only exists to support API discoverability.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| count | int64 | Number of child resources.
| path | string | Full path of the child resources. For example, for routes this is `systems/<system_id>/routes` and for trips it is `systems/<system_id>/routes/<route_id>/trips`.
| url | string | URL of the endpoint to list child resources. This is populated if the `X-Transiter-Host` HTTP header is provided in the request. See [the deployment documentation](../deployment.md#optional-setting-the-transiter-host) for more information.









## Feed

The feed resource.

Each feed is defined in the system configuration file.
Feeds are included in the public API because there are non-admin use-cases for this resource.
For example, an app might publish the staleness of realtime data
  by checking the last successful feed update time.

More detailed information on a feed -- its full configuration, and the
  current status of its periodic updates -- can be retrieved through the
  [admin API's GetSystemConfig endpoint](admin.md#get-the-config-for-a-system).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the feed, as specified in the system configuration file.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the feed resource.
| system | [System.Reference](public_resources.md#systemreference) | System corresponding to this feed. This is the parent resource in Transiter's resource hierarchy.
| last_update_ms | int64 | Number of milliseconds since the last update of this feed finished. There are three outcomes for each update: successful (new data is retrieved from the transit agency and persisted), skipped (the transit agency returned the same data as the last update, so there is nothing to do), and failed (something went wrong, e.g. the transit agency's feed is unavailable).
| last_successful_update_ms | int64 | Number of milliseconds since the last successful update of this feed finished.
| last_skipped_update_ms | int64 | Number of milliseconds since the last skipped update of this feed finished.
| last_failed_update_ms | int64 | Number of milliseconds since the last failed update of this feed finished.






#### Feed.Reference

Reference type for the feed resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.
| system | [System.Reference](public_resources.md#systemreference) | Same as the parent message.









## Resource

This message contains generic metadata that applies to all resources.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| path | string | Full path of the resource. For example, for systems this is `systems/<system_id>` and for routes it is `systems/<system_id>/routes/<route_id>`.
| url | string | URL of the resource. This is populated if the `X-Transiter-Host` HTTP header is provided in the request. See [the deployment documentation](../deployment.md#optional-setting-the-transiter-host) for more information about this header.









## Route

The Route resource.

This resource corresponds to the [route type in the GTFS static
specification](https://gtfs.org/schedule/reference/#routestxt).
Most of the fields in the resource come directly from the `routes.txt` table.
Transiter adds some additional related fields (agency, alerts)
  and computed fields (estimated headway, service maps).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the route. This is the `route_id` column in `routes.txt`.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the route resource.
| system | [System.Reference](public_resources.md#systemreference) | System corresponding to this route. This is the parent resource in Transiter's resource hierarchy.
| short_name | string | Short name of the route. This is the `route_short_name` column in `routes.txt`.
| long_name | string | Long name of the route. This is the `route_long_name` column in `routes.txt`.
| color | string | Color of the route. This is the `route_color` column in `routes.txt`.
| text_color | string | Text color of the route. This is the `route_text_color` column in `routes.txt`.
| description | string | Description of the route. This is the `route_desc` column in `routes.txt`.
| url | string | URL of a web page about the route. This is the `route_url` column in `routes.txt`.
| sort_order | int32 | Sort order of the route. This is the `route_sort_order` column in `routes.txt`.
| continuous_pickup | [Route.ContinuousPolicy](public_resources.md#routecontinuouspolicy) | Continuous pickup policy. This is the `continuous_pickup` column in `routes.txt`.
| continuous_drop_off | [Route.ContinuousPolicy](public_resources.md#routecontinuouspolicy) | Continuous dropoff policy. This is the `continuous_dropoff` column in `routes.txt`.
| type | [Route.Type](public_resources.md#routetype) | Type of the route. This is the `route_type` column in `routes.txt`.
| agency | [Agency.Reference](public_resources.md#agencyreference) | Agency this route is associated to.<br /><br />This is determined using the `agency_id` column in `routes.txt`.
| alerts | [Alert.Reference](public_resources.md#alertreference) | Active alerts for this route.<br /><br />These are determined using the `informed_entity` field in the [GTFS realtime alerts message](https://gtfs.org/realtime/feed-entities/service-alerts/#service-alerts).
| estimated_headway | int32 | An estimate of the interval of time between consecutive realtime trips, in seconds.<br /><br />If there is insufficient data to compute an estimate, the field will be empty.<br /><br />The estimate is computed as follows. For each stop that has realtime trips for the route, the list of arrival times for those trips is examined. The difference between consecutive arrival times is calculated. If there are `N` trips, there will be `N-1` such arrival time diffs. The estimated headway is the average of these diffs across all stops.
| service_maps | [Route.ServiceMap](public_resources.md#routeservicemap) | List of service maps for this route.






#### Route.ContinuousPolicy

Enum describing possible policies for continuous pickup or drop-off.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| ALLOWED | 0 | Continuous pickup or drop-off allowed. |
| NOT_ALLOWED | 1 | Continuous pickup or drop-off not allowed. |
| PHONE_AGENCY | 2 | Must phone the agency to arrange continuous pickup or drop-off. |
| COORDINATE_WITH_DRIVER | 3 | Must coordinate with driver to arrange continuous pickup or drop-off. |



#### Route.Reference

Reference type for the route resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.
| system | [System.Reference](public_resources.md#systemreference) | Same as the parent message.
| color | string | Same as the parent message.






#### Route.ServiceMap

Message describing the service maps view in routes.

See the [service maps documentation](../systems.md#service-maps) for more information on this
message and the associated field.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| config_id | string | Config ID of the service map, as specified in the system configuration file.
| stops | [Stop.Reference](public_resources.md#stopreference) | Ordered list of stops at which this route calls.<br /><br />This list may be empty, in which case the route has no service in the service map.






#### Route.Type

Enum describing possible route types.
This corresponds to possible values of the `route_type` column in `routes.txt`.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| LIGHT_RAIL | 0 |  |
| SUBWAY | 1 |  |
| RAIL | 2 |  |
| BUS | 3 |  |
| FERRY | 4 |  |
| CABLE_TRAM | 5 |  |
| AERIAL_LIFT | 6 |  |
| FUNICULAR | 7 |  |
| TROLLEY_BUS | 11 |  |
| MONORAIL | 12 |  |
| UNKNOWN | 100 |  |






## Shape

The Shape resource.

This resource corresponds to the [shape type in the GTFS static
specification](https://gtfs.org/schedule/reference/#shapestxt).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Unique ID for the shape.
| points | [Shape.ShapePoint](public_resources.md#shapeshapepoint) | Ordered list of points that make up the shape.






#### Shape.Reference

Reference type for the shape resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.






#### Shape.ShapePoint

A point within the shape.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| latitude | double | Latitude of the point.
| longitude | double | Longitude of the point.
| distance | double | Distance from the start of the shape to this point.









## Stop

The Stop resource.

This resource corresponds to the [stop type in the GTFS static
specification](https://gtfs.org/schedule/reference/#stopstxt).
Most of the static fields in the resource come directly from the `stops.txt` table.
Transiter adds some additional related fields (transfers, alerts, stop times)
  and computed fields (service maps).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the stop. This is the `stop_id` column in `stops.txt`.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the stop resource.
| system | [System.Reference](public_resources.md#systemreference) | System corresponding to this stop. This is the parent resource in Transiter's resource hierarchy.
| code | string | Code of the stop. This is the `stop_code` column in `stops.txt`.
| name | string | Name of the stop. This is the `stop_name` column in `stops.txt`.
| description | string | Description of the stop. This is the `stop_desc` column in `stops.txt`.
| zone_id | string | Zone ID of the stop. This is the `zone_id` column in `stops.txt`.
| latitude | double | Latitude of the stop. This is the `stop_lat` column in `stops.txt`.
| longitude | double | Longitude of the stop. This is the `stop_lon` column in `stops.txt`.
| url | string | URL of a webpage about the stop. This is the `stop_url` column in `stops.txt`.
| type | [Stop.Type](public_resources.md#stoptype) | Type of the stop. This is the `platform_type` column in `stops.txt`.
| parent_stop | [Stop.Reference](public_resources.md#stopreference) | Parent stop. This is determined using the `parent_station` column in `stops.txt`.
| child_stops | [Stop.Reference](public_resources.md#stopreference) | Child stops. This are determined using the `parent_station` column in `stops.txt`.
| timezone | string | Timezone of the stop. This is the `stop_timezone` column in `stops.txt`.
| wheelchair_boarding | bool | If there is wheelchair boarding for this stop. This is the `wheelchair_boarding` column in `stops.txt`.
| platform_code | string | Platform code of the stop. This is the `platform_code` column in `stops.txt`.
| service_maps | [Stop.ServiceMap](public_resources.md#stopservicemap) | List of service maps for this stop.
| alerts | [Alert.Reference](public_resources.md#alertreference) | Active alerts for this stop.<br /><br />These are determined using the `informed_entity` field in the [GTFS realtime alerts message](https://gtfs.org/realtime/reference/#message-alert).
| stop_times | [StopTime](public_resources.md#stoptime) | List of realtime stop times for this stop.<br /><br />A stop time is an event at which a trip calls at a stop.
| transfers | [Transfer](public_resources.md#transfer) | Transfers out of this stop.<br /><br />These are determined using the `from_stop_id` field in the GTFS static `transfers.txt` file.
| headsign_rules | [Stop.HeadsignRule](public_resources.md#stopheadsignrule) | List of headsign rules for this stop. See the message type for more information.






#### Stop.HeadsignRule

Message describing a headsign rule.

This message is currently only used for the New York City subway.
The data in it comes from the MTA's [subway stations feed](https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| stop | [Stop.Reference](public_resources.md#stopreference) | Stop the rule is for.
| priority | int32 | Priority of the rule (lower is higher priority).
| track | string | NYCT track.
| headsign | string | Headsign for trains arriving on the track.






#### Stop.Reference

Reference type for the stop resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.
| system | [System.Reference](public_resources.md#systemreference) | Same as the parent message.
| name | string | Same as the parent message.






#### Stop.ServiceMap

Message describing the service maps view in stops.

See the [service maps documentation](../systems.md#service-maps) for more information on this
message and the associated field.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| config_id | string | Config ID of the service map, as specified in the system configuration file.
| routes | [Route.Reference](public_resources.md#routereference) | List of routes which call at this stop.<br /><br />This list may be empty, in which case the stop has no service in the service map.






#### Stop.Type

Enum describing the possible stop types
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| STOP | 0 |  |
| STATION | 1 |  |
| ENTRANCE_OR_EXIT | 2 |  |
| GENERIC_NODE | 3 |  |
| BOARDING_AREA | 4 |  |
| PLATFORM | 5 |  |






## StopTime

Message describing a realtime stop time.

A stop time is an event in which a trip calls at a stop.
This message corresponds to the [GTFS realtime `StopTimeUpdate`
message](https://gtfs.org/realtime/reference/#message-stoptimeupdate).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| stop | [Stop.Reference](public_resources.md#stopreference) | The stop.
| trip | [Trip.Reference](public_resources.md#tripreference) | The trip.
| arrival | [StopTime.EstimatedTime](public_resources.md#stoptimeestimatedtime) | Arrival time.
| departure | [StopTime.EstimatedTime](public_resources.md#stoptimeestimatedtime) | Departure time.
| future | bool | If this stop time is in the future. This field is *not* based on the arrival or departure time. Instead, a stop time is considered in the future if it appeared in the most recent GTFS realtime feed for its trip. When this stop time disappears from the trip, Transiter marks it as in the past and freezes its data.
| stop_sequence | int32 | Stop sequence.
| headsign | string | Headsign.
| track | string | Track, from the NYCT realtime extension.






#### StopTime.EstimatedTime

Message describing the arrival or departure time of a stop time.
This corresponds to the [GTFS realtime `StopTimeEvent`
message](https://gtfs.org/realtime/reference/#message-stoptimeevent).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| time | int64 | Time of arrival.
| delay | int32 | Delay from the scheduled time.
| uncertainty | int32 | Measure of the uncertainty of the data in this message.









## System

The System resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the system as specified in the install request.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the system resource.
| name | string | Name of the system as specified in the system configuration file.
| status | [System.Status](public_resources.md#systemstatus) | Status of the system.
| agencies | [ChildResources](public_resources.md#childresources) | The system's agencies.
| feeds | [ChildResources](public_resources.md#childresources) | The system's feeds.
| routes | [ChildResources](public_resources.md#childresources) | The system's routes.
| stops | [ChildResources](public_resources.md#childresources) | The system's stops.
| transfers | [ChildResources](public_resources.md#childresources) | The system's transfers.






#### System.Reference

Reference type for the system resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.






#### System.Status

Enum describing the possible statuses of a system.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN | 0 | Unknown status, included for protobuf reasons. |
| INSTALLING | 1 | The system is currently being installed through an asynchronous install request. |
| ACTIVE | 2 | The system was successfully installed and is now active. |
| INSTALL_FAILED | 3 | The system was added through an asynchronous install request, but the install failed. |
| UPDATING | 4 | The system is currently being updated through an asynchronous update request. |
| UPDATE_FAILED | 5 | An asynchronous update of the system failed. |
| DELETING | 6 | The system is in the process of being deleted through an asynchronous delete request. |






## Transfer

The Transfer resource.

This resource corresponds to the [transfer table in the GTFS static
specification](https://gtfs.org/schedule/reference/#transferstxt).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Unique ID for the transfer. This is generated by Transiter because in the GTFS static spec transfers do not have IDs.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the transfer resource.
| system | [System.Reference](public_resources.md#systemreference) | System corresponding to this transfer. This is the parent resource in Transiter's resource hierarchy.
| from_stop | [Stop.Reference](public_resources.md#stopreference) | Beginning stop of the transfer. This is determined using the `from_stop_id` column in `transfers.txt`.
| to_stop | [Stop.Reference](public_resources.md#stopreference) | Ending stop of the transfer. This is determined using the `to_stop_id` column in `transfers.txt`.
| type | [Transfer.Type](public_resources.md#transfertype) | Type of the transfer.
| min_transfer_time | int32 | Minimum time required for the transfer, in seconds. This is the `min_transfer_time` column in `transfers.txt`.






#### Transfer.Type

Types of transfers.
The supported types are described in the documentation for the `transfer_type` column
in the GTFS static `transfers.txt` table.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| RECOMMENDED | 0 |  |
| TIMED | 1 |  |
| REQUIRES_TIME | 2 |  |
| NOT_POSSIBLE | 3 |  |






## Trip

The Trip resource.

This resource corresponds to the [trip update type in the GTFS static
specification](https://gtfs.org/realtime/reference/#message-tripupdate).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the trip.
| resource | [Resource](public_resources.md#resource) | Generic metadata about the trip resource.
| route | [Route.Reference](public_resources.md#routereference) | Route corresponding to this trip. This is the parent resource in Transiter's resource hierarchy. It is determined using the `route_id` field in the GTFS realtime feed.
| started_at | int64 | Time the trip started at.
| vehicle | [Vehicle.Reference](public_resources.md#vehiclereference) | Vehicle corresponding to the trip.
| direction_id | bool | Direction ID of the trip.
| stop_times | [StopTime](public_resources.md#stoptime) | Stop times of the trip.
| shape | [Shape.Reference](public_resources.md#shapereference) | Shape of the trip.






#### Trip.Reference

Reference type for the trip resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.
| route | [Route.Reference](public_resources.md#routereference) | Same as the parent message.
| destination | [Stop.Reference](public_resources.md#stopreference) | Same as the parent message.
| vehicle | [Vehicle.Reference](public_resources.md#vehiclereference) | Same as the parent message.
| direction_id | bool | Same as the parent message.









## Vehicle

The Vehicle resource.

This resource corresponds to the [vehicle position type in the GTFS static
specification](https://gtfs.org/realtime/reference/#message-vehicleposition).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | A unique ID for the vehicle.
| trip | [Trip.Reference](public_resources.md#tripreference) | A reference to the vehicle's trip.
| latitude | double | The vehicle's current latitude.
| longitude | double | The vehicle's current longitude.
| bearing | float | The vehicle's current bearing.
| odometer | double | The vehicle's current odometer reading.
| speed | float | The vehicle's current speed.
| stop_sequence | int32 | The stop sequence index of the vehicle's current stop.
| stop | [Stop.Reference](public_resources.md#stopreference) | A reference to the vehicle's current stop.
| current_status | [Vehicle.CurrentStatus](public_resources.md#vehiclecurrentstatus) | The vehicle's current status.
| updated_at | int64 | The timestamp of the last update to the vehicle's position.
| congestion_level | [Vehicle.CongestionLevel](public_resources.md#vehiclecongestionlevel) | The vehicle's current congestion level.
| occupancy_status | [Vehicle.OccupancyStatus](public_resources.md#vehicleoccupancystatus) | The vehicle's current occupancy status.
| occupancy_percentage | int32 | The percentage of seats occupied.






#### Vehicle.CongestionLevel

Corresponds to [CongestionLevel](https://gtfs.org/realtime/reference/#enum-congestionlevel).
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN_CONGESTION_LEVEL | 0 |  |
| RUNNING_SMOOTHLY | 1 |  |
| STOP_AND_GO | 2 |  |
| CONGESTION | 3 |  |
| SEVERE_CONGESTION | 4 |  |



#### Vehicle.CurrentStatus

Corresponds to [VehicleStopStatus](https://gtfs.org/realtime/reference/#enum-vehiclestopstatus).
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| INCOMING_AT | 0 |  |
| STOPPED_AT | 1 |  |
| IN_TRANSIT_TO | 2 |  |



#### Vehicle.OccupancyStatus

Corresponds to [OccupancyStatus](https://gtfs.org/realtime/reference/#enum-occupancystatus).
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| EMPTY | 0 |  |
| MANY_SEATS_AVAILABLE | 1 |  |
| FEW_SEATS_AVAILABLE | 2 |  |
| STANDING_ROOM_ONLY | 3 |  |
| CRUSHED_STANDING_ROOM_ONLY | 4 |  |
| FULL | 5 |  |
| NOT_ACCEPTING_PASSENGERS | 6 |  |



#### Vehicle.Reference

Reference type for the vehicle resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Same as the parent message.
| resource | [Resource](public_resources.md#resource) | Same as the parent message.









## Other types

