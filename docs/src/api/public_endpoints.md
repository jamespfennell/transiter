



# Public API endpoints


## API entrypoint

`GET /`

Provides basic information about this Transiter instance and the Transit systems it contains.

### Request type: EntrypointRequest

Request payload for the entrypoint endpoint.
	


No fields.







### Response type: EntrypointReply

Response payload for the entrypoint endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| transiter | [EntrypointReply.TransiterDetails](public_endpoints.md#EntrypointReply.TransiterDetails) | Version and other information about this Transiter binary.
| systems | [ChildResources](public_resources.md#ChildResources) | Systems that are installed in this Transiter instance.






#### EntrypointReply.TransiterDetails

Message containing version information about a Transiter binary.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| version | string | The version of the Transiter binary this instance is running.
| href | string | URL of the Transiter GitHub respository.
| build | [EntrypointReply.TransiterDetails.Build](public_endpoints.md#EntrypointReply.TransiterDetails.Build) | Information about the CI build invocation that built this Transiter binary.






#### EntrypointReply.TransiterDetails.Build

Message containing information about a specific Transiter CI build.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| number | string | The GitHub build number.
| built_at | string | Time the binary was built, in the form of a human readable string.
| built_at_timestamp | string | Time the binary was built, in the form of a Unix timestamp.
| git_commit_hash | string | Hash of the Git commit that the binary was built at.
| href | string | URL of the GitHub actions CI run.








## List systems

`GET /systems`

List all transit systems that are installed in this Transiter instance.

### Request type: ListSystemsRequest

Request payload for the list systems endpoint.
	


No fields.







### Response type: ListSystemsReply

Response payload for the list systems endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| systems | [System](public_resources.md#System) | List of systems.








## Get system

`GET /systems/<system_id>`

Get a system by its ID.

### Request type: GetSystemRequest

Request payload for the get system endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system to get.<br /><br />This is a URL parameter in the HTTP API.








### Response type: [System](public_resources.md#System)

## List agencies

`GET /systems/<system_id>/agencies`

List all agencies in a system.

### Request type: ListAgenciesRequest

Request payload for the list agencies endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list agencies.<br /><br />This is a URL parameter in the HTTP API.








### Response type: ListAgenciesReply

Response payload for the list agencies endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| agencies | [Agency](public_resources.md#Agency) | List of agencies.








## Get agency

`GET /systems/<system_id>/agencies/<agency_id>`

Get an agency in a system by its ID.

### Request type: GetAgencyRequest

Request payload for the get agency endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the agency is in.<br /><br />This is a URL parameter in the HTTP API.
| agency_id | string | ID of the agency.<br /><br />This is a URL parameter in the HTTP API.








### Response type: [Agency](public_resources.md#Agency)

## List stops

`GET /systems/<system_id>/stops`

List all stops in a system.

This endpoint is paginated.
If there are more results, the `next_id` field of the response will be populated.
To get more results, make the same request with the `first_id` field set to the value of `next_id` in the response.

### Request type: ListStopsRequest

Request payload for the list stops endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list stops.<br /><br />This is a URL parameter in the HTTP API.
| search_mode | [ListStopsRequest.SearchMode](public_resources.md#ListStopsRequest.SearchMode) | The type of search to perform when listing stops.
| only_return_specified_ids | bool | If true, only return stops whose IDs are specified in the repeated `id` field. Only supported when the search mode is ID.
| id | string | IDs to return if `only_return_specified_ids` is set to true. It is an error to populate this field if `only_return_specified_ids` is false. Only supported when the search mode is ID.
| first_id | string | ID of the first stop to return. If not set, the stop with the smallest ID will be first. Only supported when the search mode is ID.
| limit | int32 | Maximum number of stops to return. This is supported in all search modes. For performance reasons, if it is larger than 100 it is rounded down to 100.
| skip_stop_times | bool | If true, the stop times field will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.
| skip_transfers | bool | If true, the transfers field will not be populated. This will generally make the response faster to generate.
| max_distance | double | The maximum distance in kilometers that a stop must be from latitude, longitude to be listed when using DISTANCE search mode.
| latitude | double | The latitude relative to the returned stops when using DISTANCE search mode.
| longitude | double | The longitude relative to the returned stops when using DISTANCE search mode.






#### ListStopsRequest.SearchMode

The possible search modes when listing stops.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| ID | 0 | Return a paginated list of stops sorted by stop ID. |
| DISTANCE | 1 | Return all stops within max_distance of (latitude, longitude), sorted by the distance. |





### Response type: ListStopsReply

Response payload for the list stops endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| stops | [Stop](public_resources.md#Stop) | List of stops.
| next_id | string | ID of the next stop to return, if there are more results.








## Get stop

`GET /systems/<system_id>/stops/<stop_id>`

Get a stop in a system by its ID.

### Request type: GetStopRequest

Reqeust payload for the get stop endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the stop is in.<br /><br />This is a URL parameter in the HTTP API.
| stop_id | string | ID of the stop.<br /><br />This is a URL parameter in the HTTP API.
| skip_stop_times | bool | If true, the stop times field will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.
| skip_transfers | bool | If true, the transfers field will not be populated. This will generally make the response faster to generate.








### Response type: [Stop](public_resources.md#Stop)

## List routes

`GET /systems/<system_id>/routes`

List all routes in a system.

### Request type: ListRoutesRequest

Request payload for the list routes endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list routes.<br /><br />This is a URL parameter in the HTTP API.
| skip_estimated_headways | bool | If true, the estimated headway fields will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.








### Response type: ListRoutesReply

Response payload for the list routes endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| routes | [Route](public_resources.md#Route) | List of routes.








## Get route

`GET /systems/<system_id>/routes/<route_id>`

Get a route in a system by its ID.

### Request type: GetRouteRequest

Request payload for the get route endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the route is in.<br /><br />This is a URL parameter in the HTTP API.
| route_id | string | ID of the route.<br /><br />This is a URL parameter in the HTTP API.
| skip_estimated_headways | bool | If true, the estimated headway field will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.








### Response type: [Route](public_resources.md#Route)

## List trips

`GET /systems/<system_id>/routes/<route_id>/trips`

List all trips in a route.

### Request type: ListTripsRequest

Request payload for the list trips endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the route is in.<br /><br />This is a URL parameter in the HTTP API.
| route_id | string | ID of the route for which to list trips<br /><br />This is a URL parameter in the HTTP API.








### Response type: ListTripsReply

Response payload for the list trips endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| trips | [Trip](public_resources.md#Trip) | List of trips.








## Get trip

`GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`

Get a trip by its ID.

### Request type: GetTripRequest

Request payload for the get trip endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the trip is in.<br /><br />This is a URL parameter in the HTTP API.
| route_id | string | ID of the route the trip is in.<br /><br />This is a URL parameter in the HTTP API.
| trip_id | string | ID of the route.<br /><br />This is a URL parameter in the HTTP API.








### Response type: [Trip](public_resources.md#Trip)

## List alerts

`GET /systems/<system_id>/alerts`

List all alerts in a system.
By default this endpoint returns both active alerts
  (alerts which have an active period containing the current time) and non-active alerts.

### Request type: ListAlertsRequest

Request payload for the list alerts endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list alerts.<br /><br />This is a URL parameter in the HTTP API.
| alert_id | string | If non-empty, only alerts with the provided IDs are returned. This is interpreted as a filtering condition, so it is not an error to provide non-existent IDs.<br /><br />If empty, all alerts in the system are returned. TODO: add a boolean filter_on_alert_ids field








### Response type: ListAlertsReply

Response payload for the list alerts endpoiont.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| alerts | [Alert](public_resources.md#Alert) | List of alerts.








## Get alert

`GET /systems/<system_id>/alerts/<alert_id>`

Get an alert by its ID.

### Request type: GetAlertRequest

Request payload for the get alert endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the alert is in.<br /><br />This is a URL parameter in the HTTP API.
| alert_id | string | ID of the alert.<br /><br />This is a URL parameter in the HTTP API.








### Response type: [Alert](public_resources.md#Alert)

## List transfers

`GET /systems/<system_id>/transfers`

List all transfers in a system.

### Request type: ListTransfersRequest

Request payload for the list transfers endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list transfers.








### Response type: ListTransfersReply

Response payload for the list transfers endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| transfers | [Transfer](public_resources.md#Transfer) | List of transfers.








## List feeds

`GET /systems/<system_id>/feeds`

List all feeds for a system.

### Request type: ListFeedsRequest

Request payload for the list feeds endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list feeds.








### Response type: ListFeedsReply

Response payload for the list feeds endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| feeds | [Feed](public_resources.md#Feed) | List of feeds.








## Get feed

`GET /systems/<system_id>/feeds/<feed_id>`

Get a feed in a system by its ID.

### Request type: GetFeedRequest

Request payload for the get feed endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the feed is in.<br /><br />This is a URL parameter in the HTTP API.
| feed_id | string | ID of the feed.<br /><br />This is a URL parameter in the HTTP API.








### Response type: [Feed](public_resources.md#Feed)

## List vehicles

`GET /systems/<system_id>/vehicles`

List all feeds for a system.

### Request type: ListVehiclesRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list vehicles.
| search_mode | [ListVehiclesRequest.SearchMode](public_resources.md#ListVehiclesRequest.SearchMode) | The type of search to perform when listing vehicles.
| only_return_specified_ids | bool | If true, only return vehicles whose IDs are specified in the repeated `id` field. Only supported when the search mode is ID.
| id | string | IDs to return if `only_return_specified_ids` is set to true. It is an error to populate this field if `only_return_specified_ids` is false. Only supported when the search mode is ID.
| first_id | string | ID of the first vehicle to return. If not set, the vehicle with the smallest ID will be first. Only supported when the search mode is ID.
| limit | int32 | Maximum number of vehicles to return. This is supported in all search modes. For performance reasons, if it is larger than 100 it is rounded down to 100.
| max_distance | double | The maximum distance in kilometers that a vehicle must be from latitude, longitude to be listed when using DISTANCE search mode.
| latitude | double | The latitude relative to the returned vehicles when using DISTANCE search mode.
| longitude | double | The longitude relative to the returned vehicles when using DISTANCE search mode.






#### ListVehiclesRequest.SearchMode


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| ID | 0 | Return a paginated list of vehicles sorted by vehicle ID. |
| DISTANCE | 1 | Return all vehicles within max_distance of (latitude, longitude), sorted by the distance. |





### Response type: ListVehiclesReply


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| vehicles | [Vehicle](public_resources.md#Vehicle) | List of vehicles.
| next_id | string | ID of the next vehicle to return, if there are more results.








## Get vehicle

`GET /systems/<system_id>/vehicles/<vehicle_id>`

Get a vehicle in a system by its ID.

### Request type: GetVehicleRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the vehicle is in.<br /><br />This is a URL parameter in the HTTP API.
| vehicle_id | string | ID of the vehicle.<br /><br />This is a URL parameter in the HTTP API.








### Response type: [Vehicle](public_resources.md#Vehicle)




