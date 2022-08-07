

# Public API resources

Public API

The Transiter public API is based around hierarchal resources, like many REST APIs.
This is the resource hierarchy:

```
System
|- Agency
|- Alert
|- Feed
|   |- Feed update
|- Route
|   |- Trip
|       |- Vehicle with no ID
|- Stop
|- Transfer
|- Vehicle with ID
```

For each resource there is a proto message type, a list endpoint, and a get endpoints.
For stops, the message is [Stop](#stoppreview), the list endpoint is [ListStops], and the get endpoint is [GetStop].

The URLs in the HTTP API are determined by the hierarchy; thus:

- List all systems has URL `/systems`,
- Get system with ID `<system_id>` has URL `/systems/<system_id>`,
- List all routes in the system has URL `/systems/<system_id>/routes`,
- Get route has URL `/systems/<system_id>/routes/<route_id>`,

and so on.

Many resources refer to other resources across the hierarchy.
For example, each route has an agency it is attached to.
Each stop has a list of service maps, each of which contains a set of routes.
In these situations the resource message contains a _preview_ of the other resource.
The [Route](#route) message contains an agency preview, in the form of an [Agency.Preview](#agencypreview)
message.
These preview messages contain at least enough information to uniquely identify the resource.
However they also contain additional information that is considered generally useful;
thus, the [Stop.Preview](#stoppreview) message contains the stop's name.
What counts as "considered generally" is obviously very subjective and open to change.

The following table summarizes all of the resources and their types.
The right-most column describes the source_of the resource.
The public API is a read-only API so all of the resources come from somewhere else.

| Resource    | Preview type | List endpoint | Get endpoint | Source |
| ----------- | --------------- | ---------- | ------------------ | -------|
| [Agency](#agency)   | [Agency.Preview](#agencypreview) | [GetAgency] | [ListAgency]  | GTFS static    
| Alert       | System          | [Alert]    | [Alert.Preview]    | GTFS realtime 
| Feed        | System          |            |                    | system config  
| Feed update | Feed            |            |                    | Transiter update process
| Route       | System          |            |                    | GTFS static
| Trip        | Route           |            |                    | GTFS realtime      
| Stop        | System          |            |                    | GTFS static   
| System      | None            |            |                    | system config
| Transfer    | System          |            |                    | GTFS static       
| Vehicle     | System or trip  |            |                    | GTFS realtime



## Agency

The Agency resource.

This resource corresponds to the [agency type in the GTFS static
specification](https://developers.google.com/transit/gtfs/reference#agencytxt).
Most of the fields in the resource come directly from the `agency.txt` table.
Transiter adds some additional related fields (alerts).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the agency. This is the `agency_id` column in `agency.txt`.
| name | string | Name of the agency. This is the `agency_name` column in `agency.txt`.
| url | string | URL of the agency. This is the `agency_url` column in `agency.txt`.
| timezone | string | Timezone of the agency. This is the `agency_timezone` column in `agency.txt`.
| language | string | Language of the agency. This is the `agency_lang` column in `agency.txt`.
| phone | string | Phone number of the agency. This is the `agency_phone` column in `agency.txt`.
| fare_url | string | URL where tickets for the agency's services ban be bought. This is the `agency_fare_url` column in `agency.txt`.
| email | string | Email address of the agency. This is the `agency_email` column in `agency.txt`.
| routes | [Route.Preview](public_resources.md#Route.Preview) | TODO: this should be its own endpoint I think
| alerts | [Alert.Preview](public_resources.md#Alert.Preview) | List of active alerts for the agency.<br /><br />These are determined using the `informed_entity` field in the [GTFS realtime alerts message](https://developers.google.com/transit/gtfs-realtime/reference#message-alert).
| href | string | 






#### Agency.Preview

Preview contains preview information about the agency.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| name | string | 
| href | string | 









## Alert

The Alert resource.

This resource corresponds to the [alert type in the GTFS realtime
specification](https://developers.google.com/transit/gtfs-realtime/reference#message-alert).

TODO: informed entites
TODO; alphabetize the messages
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the alert. This corresponds to the [ID field in the feed entity message](https://developers.google.com/transit/gtfs-realtime/reference#message-feedentity) corresponding to the alert.
| cause | [Alert.Cause](public_resources.md#Alert.Cause) | Cause of the alert. This corresponds to the `cause` field in the realtime alert message.
| effect | [Alert.Effect](public_resources.md#Alert.Effect) | Effect of the alert. This corresponds to the `effect` field in the realtime alert message.
| current_active_period | [Alert.ActivePeriod](public_resources.md#Alert.ActivePeriod) | The current active period, if the alert is currently active. If the alert is not active this is empty.
| all_active_periods | [Alert.ActivePeriod](public_resources.md#Alert.ActivePeriod) | All active periods for this alert. Transiter guarantees that these active periods have no overlap.
| header | [Alert.Text](public_resources.md#Alert.Text) | Header of the alert, in zero or more languages. This corresponds to the `header_text` field in the realtime alert message.
| description | [Alert.Text](public_resources.md#Alert.Text) | Description of the alert, in zero or more languages. This corresponds to the `description_text` field in the realtime alert message.
| url | [Alert.Text](public_resources.md#Alert.Text) | URL for additional information about the alert, in zero or more languages. This corresponds to the `url` field in the realtime alert message.






#### Alert.ActivePeriod

The active period message describes a period when an alert is active.
It corresponds the the [time range message in the GTFS realtime
specification](https://developers.google.com/transit/gtfs-realtime/reference#message-timerange).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| starts_at | int64 | Unix timestamp of the start time of the active period. If not set, the alert be interpreted as being always active up to the end time.
| ends_at | int64 | Unix timestamp of the end time of the active period. If not set, the alert be interpreted as being indefinitely active.






#### Alert.Cause

Cause is the same as the [cause enum in the GTFS realtime
specification](https://developers.google.com/transit/gtfs-realtime/reference#enum-cause),
except `UNKNOWN_CAUSE` has value 0 instead of 1 to satisfy proto3 requirements.
	



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
specification](https://developers.google.com/transit/gtfs-realtime/reference#enum-effect),
except `UNKNOWN_EFFECT` has value 0 instead of 1 to satisfy proto3 requirements.
	



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



#### Alert.Preview

TODO: rename Preview to Reference?
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| cause | [Alert.Cause](public_resources.md#Alert.Cause) | 
| effect | [Alert.Effect](public_resources.md#Alert.Effect) | TODO(APIv2): add this field and create API endpoints optional string href = 3;






#### Alert.Text

The text message describes an alert header/description/URL in a specified language.
It corresponds the the [translation message in the GTFS realtime
specification](https://developers.google.com/transit/gtfs-realtime/reference#message-translation).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| text | string | Content of the text.
| language | string | Language of this text.









## Feed

The feed resource.

Each feed is defined in the system configuration file.
Feeds are included in the public API because there are non-admin use-cases for this resource.
For example, an app might publish the staleness of realtime data
  by checking for the last succesful feed update.

More detailed information on a feed -- its full configuration, and the
  current status of its periodic updates -- can be retrieved through the admin API.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the feed, as specified in the system configuration file.
| periodic_update_enabled | bool | Whether periodic update is enabled for this feed.
| periodic_update_period | string | If periodic update is enabled, the period each update is triggered.
| updates | [Feed.Updates](public_resources.md#Feed.Updates) | 






#### Feed.Preview

Preview contains preview information about the feed.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| periodic_update_enabled | bool | TODO: remove
| periodic_update_period | string | TODO: remove
| href | string | 






#### Feed.Updates

TODO: have a ChildResources message and use that instead
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| href | string | 









## FeedUpdate

The feed update resource.

Each feed update event
  -- triggered manually though the admin API, or automatically by the scheduler --
generates a feed update resource.
This resource is updated as the feed update progresses.
A background task in Transiter periodically garbage collects old updates.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the feed update. This is the primary key of the associated Postgres database row so it's actually globally unique.
| type | string | TODO: make these enums Type of the feed update.
| status | string | Status of the feed update.
| result | string | TODO what is this?
| stack_trace | string | TODO: delete?
| content_length | int32 | Number of bytes in the downloaded feed data.
| content_hash | string | Hash of the downloaded feed data. This is used to skip updates if the feed data hasn't changed.
| completed_at | int64 | Unix timestamp of the approximate time the update completed. TODO: started_at? scheduled_at?









## Route

The Route resource.

This resource corresponds to the [route type in the GTFS static
specification](https://developers.google.com/transit/gtfs/reference#routestxt).
Most of the fields in the resource come directly from the `routes.txt` table.
Transiter adds some additional related fields (agency, alerts)
  and computed fields (estimated headway, service maps).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the route. This is the `route_id` column in `routes.txt`.
| short_name | string | Short name of the route. This is the `route_short_name` column in `routes.txt`.
| long_name | string | Long name of the route. This is the `route_long_name` column in `routes.txt`.
| color | string | Color of the route. This is the `route_color` column in `routes.txt`.
| text_color | string | Text color of the route. This is the `route_text_color` column in `routes.txt`.
| description | string | Description of the route. This is the `route_desc` column in `routes.txt`.
| url | string | URL of a web page about the route. This is the `route_url` column in `routes.txt`.
| sort_order | int32 | Sort order of the route. This is the `route_sort_order` column in `routes.txt`.
| continuous_pickup | string | TODO: make these 3 fields enums Continuous pickup policy. This is the `continuous_pickup` column in `routes.txt`.
| continuous_drop_off | string | Continuous dropoff policy. This is the `continuous_dropoff` column in `routes.txt`.
| type | string | Type of the route. This is the `route_type` column in `routes.txt`.
| agency | [Agency.Preview](public_resources.md#Agency.Preview) | Agency this route is associated to.<br /><br />This is determined using the `agency_id` column in `routes.txt`.
| alerts | [Alert.Preview](public_resources.md#Alert.Preview) | Active alerts for this route.<br /><br />These are determined using the `informed_entity` field in the [GTFS realtime alerts message](https://developers.google.com/transit/gtfs-realtime/reference#message-alert).
| estimated_headway | int32 | An estimate of the interval of time between consecutive realtime trips, in seconds.<br /><br />If there is insufficient data to compute an estimate, the field will be empty.<br /><br />The estimate is computed as follows. For each stop that has realtime trips for the route, the list of arrival times for those trips is examined. The difference between consecutive arrival times is calculated. If there are `N` trips, there will be `N-1` such arrival time diffs. The estimated headway is the average of these diffs across / all stops.
| service_maps | [Route.ServiceMap](public_resources.md#Route.ServiceMap) | List of service maps for this route.






#### Route.Preview

Preview contains preview information about the route.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| color | string | TODO(APIv2): remove? or add text_color?
| system | [System](public_resources.md#System) | Will be populated only if the system is not obvious TODO: maybe we should just include it always so that each preview/reference uniquely identifies a resource
| href | string | 






#### Route.ServiceMap

Message describing the service maps view in routes.

See the service maps documentation for more information on this
message and the associated field.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| config_id | string | Config ID of the service map, as specified in the system configuration file.
| stops | [Stop.Preview](public_resources.md#Stop.Preview) | Ordered list of stop at which this route calls.<br /><br />This list may be empty, in which case the route has no service in the service map.









## Stop

The Stop resource.

This resource corresponds to the [stop type in the GTFS static
specification](https://developers.google.com/transit/gtfs/reference#stopstxt).
Most of the static fields in the resource come directly from the `stops.txt` table.
Transiter adds some additional related fields (transfers, alerts, stop times)
  and computed fields (service maps).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the stop. This is the `stop_id` column in `stops.txt`.
| code | string | Code of the stop. This is the `stop_code` column in `stops.txt`.
| name | string | Name of the stop. This is the `stop_name` column in `stops.txt`.
| description | string | Description of the stop. This is the `stop_desc` column in `stops.txt`.
| zone_id | string | Zone ID of the stop. This is the `zone_id` column in `stops.txt`.
| latitude | double | Latitude of the stop. This is the `stop_lat` column in `stops.txt`.
| longitude | double | Longitude of the stop. This is the `stop_lon` column in `stops.txt`.
| url | string | URL of a webpage about the stop. This is the `stop_url` column in `stops.txt`.
| type | [Stop.Type](public_resources.md#Stop.Type) | Type of the stop. This is the `platform_type` column in `stops.txt`.
| parent_stop | [Stop.Preview](public_resources.md#Stop.Preview) | Parent stop. This is determined using the `parent_station` column in `stops.txt`.
| child_stops | [Stop.Preview](public_resources.md#Stop.Preview) | Child stops. This are determined using the `parent_station` column in `stops.txt`.
| timezone | string | Timezone of the stop. This is the `stop_timezone` column in `stops.txt`.
| wheelchair_boarding | bool | If there is wheelchair boarding for this stop. This is the `wheelchair_boarding` column in `stops.txt`.
| platform_code | string | Platform code of the stop. This is the `platform_code` column in `stops.txt`.
| service_maps | [Stop.ServiceMap](public_resources.md#Stop.ServiceMap) | List of service maps for this stop.
| alerts | [Alert.Preview](public_resources.md#Alert.Preview) | Active alerts for this stop.<br /><br />These are determined using the `informed_entity` field in the [GTFS realtime alerts message](https://developers.google.com/transit/gtfs-realtime/reference#message-alert).
| stop_times | [StopTime](public_resources.md#StopTime) | List of realtime stop times for this stop.<br /><br />A stop time is an event at which a trip calls at a stop.
| transfers | [Transfer](public_resources.md#Transfer) | Transfers out of this stop.<br /><br />These are determined using the `from_stop_id` field in the GTFS static `transfers.txt` file.
| headsign_rules | [Stop.HeadsignRule](public_resources.md#Stop.HeadsignRule) | List of headsign rules for this stop.






#### Stop.HeadsignRule

Message describing a headsign rule.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| stop | [Stop.Preview](public_resources.md#Stop.Preview) | Stop the rule is for.
| priority | int32 | Priority of the rule (lower is higher priority).
| track | string | NYCT track.
| headsign | string | Headsign.






#### Stop.Preview

Preview contains preview information about the stop.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| name | string | TODO: make optional
| href | string | 






#### Stop.ServiceMap

Message describing the service maps view in stops.

See the service maps documentation for more information on this
message and the associated field.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| config_id | string | Config ID of the service map, as specified in the system configuration file.
| routes | [Route.Preview](public_resources.md#Route.Preview) | List of routes which call at this stop.<br /><br />This list may be empty, in which case the stop has no service in the service map.






#### Stop.Type

Enum describing the possible stop types
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| STOP | 0 |  |
| STATION | 1 |  |
| ENTRANCE_OR_EXIT | 2 |  |
| GENERIC_NODE | 3 |  |
| BOARDING_AREA | 4 |  |






## StopTime

Message describing a realtime stop time.

A stop time is an event in which a trip calls at a stop.
This message corresponds to the [GTFS realtime `StopTimeUpdate`
message](https://developers.google.com/transit/gtfs-realtime/reference#message-stoptimeupdate)
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| stop | [Stop.Preview](public_resources.md#Stop.Preview) | The stop.
| trip | [Trip.Preview](public_resources.md#Trip.Preview) | The trip.
| arrival | [StopTime.EstimatedTime](public_resources.md#StopTime.EstimatedTime) | Arrival time.
| departure | [StopTime.EstimatedTime](public_resources.md#StopTime.EstimatedTime) | Departure time.
| future | bool | If this stop time is in the future. This field is *not* based on the arrival or departure time. Instead, a stop time is considered in the future if it appeared in the most recent GTFS realtime feed for its trip. When this stop time disappears from the trip, Transiter marks it as past and freezes its data.
| stop_sequence | int32 | Stop sequence.
| headsign | string | Headsign.
| track | string | Track, from the NYCT realtime extension.






#### StopTime.EstimatedTime

Message describing the arrival or departure time of a stop time.
This corresponds to the [GTFS realtime `StopTimeEvent`
message](https://developers.google.com/transit/gtfs-realtime/reference#message-stoptimeevent).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| time | int64 | 
| delay | int32 | 
| uncertainty | int32 | 









## System

The System resource.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | ID of the system as specified in the install request.
| name | string | Name of the system as specified in the system configuration file.
| status | [System.Status](public_resources.md#System.Status) | Status of the system.
| agencies | [System.ChildEntities](public_resources.md#System.ChildEntities) | 
| feeds | [System.ChildEntities](public_resources.md#System.ChildEntities) | 
| routes | [System.ChildEntities](public_resources.md#System.ChildEntities) | 
| stops | [System.ChildEntities](public_resources.md#System.ChildEntities) | 
| transfers | [System.ChildEntities](public_resources.md#System.ChildEntities) | 
| href | string | 






#### System.ChildEntities

TODO: rename `ChildResources`, move out of here, and reuse
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| count | int64 | 
| href | string | 






#### System.Preview

Preview contains preview information about the system.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| href | string | 






#### System.Status

Enum describing the possible statuses of a system.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN | 0 | Unknown status, included for protobuf reasons. |
| INSTALLING | 1 | The system is currently being installed through an asychronous install request. |
| ACTIVE | 2 | The system was successfully installed and is now active. |
| INSTALL_FAILED | 3 | The system was added through an asynchronous install request, but the install failed. |
| UPDATING | 4 | The system is currently being updated through an asynchronous update request. |
| UPDATE_FAILED | 5 | An asynchronous update of the system failed. |
| DELETING | 6 | The system is in the process of being deleted through an asynchronous delete request. |






## Transfer


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| from_stop | [Stop.Preview](public_resources.md#Stop.Preview) | 
| to_stop | [Stop.Preview](public_resources.md#Stop.Preview) | 
| type | [Transfer.Type](public_resources.md#Transfer.Type) | 
| min_transfer_time | int32 | 
| distance | int32 | 






#### Transfer.Type


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| RECOMMENDED | 0 |  |
| TIMED | 1 |  |
| REQUIRES_TIME | 2 |  |
| NO_POSSIBLE | 3 |  |






## Trip


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| route | [Route.Preview](public_resources.md#Route.Preview) | TODO(APIv2): remove route?
| last_stop | [Stop.Preview](public_resources.md#Stop.Preview) | TODO: remove?
| started_at | int64 | 
| vehicle | [Vehicle.Preview](public_resources.md#Vehicle.Preview) | 
| direction_id | bool | 
| stop_times | [StopTime](public_resources.md#StopTime) | 
| href | string | 






#### Trip.Preview

Preview contains preview information about the trip.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| route | [Route.Preview](public_resources.md#Route.Preview) | 
| destination | [Stop.Preview](public_resources.md#Stop.Preview) | 
| vehicle | [Vehicle.Preview](public_resources.md#Vehicle.Preview) | 
| href | string | 









## Vehicle


	


No fields.





#### Vehicle.Preview

Preview contains preview information about the vehice.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 









## Other types

