



# Public API endpoints


## API entrypoint

`GET /`

Provides basic information about this Transiter instance and the transit systems it contains.

### Request: EntrypointRequest

Request payload for the entrypoint endpoint.
	


No fields.







### Response: EntrypointReply

Response payload for the entrypoint endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| transiter | [EntrypointReply.TransiterDetails](public_endpoints.md#entrypointreplytransiterdetails) | Version and other information about this Transiter binary.
| systems | [ChildResources](public_resources.md#childresources) | Systems that are installed in this Transiter instance.






#### EntrypointReply.TransiterDetails

Message containing version information about a Transiter binary.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| version | string | The version of the Transiter binary this instance is running.
| url | string | URL of the Transiter GitHub repository.








## List systems

`GET /systems`

List all transit systems that are installed in this Transiter instance.

### Request: ListSystemsRequest

Request payload for the list systems endpoint.
	


No fields.







### Response: ListSystemsReply

Response payload for the list systems endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| systems | [System](public_resources.md#system) | List of systems.








## Get system

`GET /systems/<system_id>`

Get a system by its ID.

### Request: GetSystemRequest

Request payload for the get system endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system to get.<br /><br />This is a URL parameter in the HTTP API.








### Response: [System](public_resources.md#system)

## List agencies

`GET /systems/<system_id>/agencies`

List all agencies in a system.

### Request: ListAgenciesRequest

Request payload for the list agencies endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list agencies.<br /><br />This is a URL parameter in the HTTP API.








### Response: ListAgenciesReply

Response payload for the list agencies endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| agencies | [Agency](public_resources.md#agency) | List of agencies.








## Get agency

`GET /systems/<system_id>/agencies/<agency_id>`

Get an agency in a system by its ID.

### Request: GetAgencyRequest

Request payload for the get agency endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the agency is in.<br /><br />This is a URL parameter in the HTTP API.
| agency_id | string | ID of the agency.<br /><br />This is a URL parameter in the HTTP API.








### Response: [Agency](public_resources.md#agency)

## List stops

`GET /systems/<system_id>/stops`

List all stops in a system.

This endpoint is paginated.
If there are more results, the `next_id` field of the response will be populated.
To get more results, make the same request with the `first_id` field set to the value of `next_id` in the response.

### Request: ListStopsRequest

Request payload for the list stops endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list stops.<br /><br />This is a URL parameter in the HTTP API.
| search_mode | [ListStopsRequest.SearchMode](public_endpoints.md#liststopsrequestsearchmode) | The type of search to perform when listing stops.
| only_return_specified_ids | bool | Deprecated: use `filter_by_id` instead.
| filter_by_id | bool | If true, only return stops whose IDs are specified in the repeated `id` field. Only supported when the search mode is ID.
| id | string | IDs to return if `filter_by_id` is set to true. It is an error to populate this field if `filter_by_id` is false. Only supported when the search mode is ID.
| filter_by_type | bool | If true, only return stops whose types are specified in the repeated `type` field.
| type | [Stop.Type](public_resources.md#stoptype) | Types to filter by if `filter_by_type` is set to true. It is an error to populate this field if `filter_by_id` is false.
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





### Response: ListStopsReply

Response payload for the list stops endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| stops | [Stop](public_resources.md#stop) | List of stops.
| next_id | string | ID of the next stop to return, if there are more results.








## Get stop

`GET /systems/<system_id>/stops/<stop_id>`

Get a stop in a system by its ID.

### Request: GetStopRequest

Request payload for the get stop endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the stop is in.<br /><br />This is a URL parameter in the HTTP API.
| stop_id | string | ID of the stop.<br /><br />This is a URL parameter in the HTTP API.
| skip_stop_times | bool | If true, the stop times field will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.
| skip_transfers | bool | If true, the transfers field will not be populated. This will generally make the response faster to generate.








### Response: [Stop](public_resources.md#stop)

## List routes

`GET /systems/<system_id>/routes`

List all routes in a system.

### Request: ListRoutesRequest

Request payload for the list routes endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list routes.<br /><br />This is a URL parameter in the HTTP API.
| skip_estimated_headways | bool | If true, the estimated headway fields will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.








### Response: ListRoutesReply

Response payload for the list routes endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| routes | [Route](public_resources.md#route) | List of routes.








## Get route

`GET /systems/<system_id>/routes/<route_id>`

Get a route in a system by its ID.

### Request: GetRouteRequest

Request payload for the get route endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the route is in.<br /><br />This is a URL parameter in the HTTP API.
| route_id | string | ID of the route.<br /><br />This is a URL parameter in the HTTP API.
| skip_estimated_headways | bool | If true, the estimated headway field will not be populated. This will generally make the response faster to generate.
| skip_service_maps | bool | If true, the service maps field will not be populated. This will generally make the response faster to generate.
| skip_alerts | bool | If true, the alerts field will not be populated. This will generally make the response faster to generate.








### Response: [Route](public_resources.md#route)

## List trips

`GET /systems/<system_id>/routes/<route_id>/trips`

List all trips in a route.

### Request: ListTripsRequest

Request payload for the list trips endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the route is in.<br /><br />This is a URL parameter in the HTTP API.
| route_id | string | ID of the route for which to list trips<br /><br />This is a URL parameter in the HTTP API.








### Response: ListTripsReply

Response payload for the list trips endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| trips | [Trip](public_resources.md#trip) | List of trips.








## Get trip

`GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`

Get a trip by its ID.

### Request: GetTripRequest

Request payload for the get trip endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the trip is in.<br /><br />This is a URL parameter in the HTTP API.
| route_id | string | ID of the route the trip is in.<br /><br />This is a URL parameter in the HTTP API.
| trip_id | string | ID of the route.<br /><br />This is a URL parameter in the HTTP API.








### Response: [Trip](public_resources.md#trip)

## List alerts

`GET /systems/<system_id>/alerts`

List all alerts in a system.
By default this endpoint returns both active alerts
  (alerts which have an active period containing the current time) and non-active alerts.

### Request: ListAlertsRequest

Request payload for the list alerts endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list alerts.<br /><br />This is a URL parameter in the HTTP API.
| alert_id | string | If non-empty, only alerts with the provided IDs are returned. This is interpreted as a filtering condition, so it is not an error to provide non-existent IDs.<br /><br />If empty, all alerts in the system are returned. TODO: add a boolean filter_on_alert_ids field








### Response: ListAlertsReply

Response payload for the list alerts endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| alerts | [Alert](public_resources.md#alert) | List of alerts.








## Get alert

`GET /systems/<system_id>/alerts/<alert_id>`

Get an alert by its ID.

### Request: GetAlertRequest

Request payload for the get alert endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the alert is in.<br /><br />This is a URL parameter in the HTTP API.
| alert_id | string | ID of the alert.<br /><br />This is a URL parameter in the HTTP API.








### Response: [Alert](public_resources.md#alert)

## List transfers

`GET /systems/<system_id>/transfers`

List all transfers in a system.

### Request: ListTransfersRequest

Request payload for the list transfers endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list transfers.








### Response: ListTransfersReply

Response payload for the list transfers endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| transfers | [Transfer](public_resources.md#transfer) | List of transfers.








## Get transfer

`GET /systems/<system_id>/transfers/<transfer_id>`

Get a transfer by its ID.

### Request: GetTransferRequest

Request payload for the get transfer endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the transfer is in.<br /><br />This is a URL parameter in the HTTP API.
| transfer_id | string | ID of the transfer.<br /><br />This is a URL parameter in the HTTP API.








### Response: [Transfer](public_resources.md#transfer)

## List feeds

`GET /systems/<system_id>/feeds`

List all feeds for a system.

### Request: ListFeedsRequest

Request payload for the list feeds endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list feeds.








### Response: ListFeedsReply

Response payload for the list feeds endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| feeds | [Feed](public_resources.md#feed) | List of feeds.








## Get feed

`GET /systems/<system_id>/feeds/<feed_id>`

Get a feed in a system by its ID.

### Request: GetFeedRequest

Request payload for the get feed endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the feed is in.<br /><br />This is a URL parameter in the HTTP API.
| feed_id | string | ID of the feed.<br /><br />This is a URL parameter in the HTTP API.








### Response: [Feed](public_resources.md#feed)

## List vehicles

`GET /systems/<system_id>/vehicles`

List all feeds for a system.

### Request: ListVehiclesRequest

Request payload for the list vehicles endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system for which to list vehicles.
| search_mode | [ListVehiclesRequest.SearchMode](public_endpoints.md#listvehiclesrequestsearchmode) | The type of search to perform when listing vehicles.
| only_return_specified_ids | bool | Deprecated: use `filter_by_id` instead.
| filter_by_id | bool | If true, only return vehicles whose IDs are specified in the repeated `id` field. Only supported when the search mode is ID.
| id | string | IDs to return if `filter_by_id` is set to true. It is an error to populate this field if `filter_by_id` is false. Only supported when the search mode is ID.
| first_id | string | ID of the first vehicle to return. If not set, the vehicle with the smallest ID will be first. Only supported when the search mode is ID.
| limit | int32 | Maximum number of vehicles to return. This is supported in all search modes. For performance reasons, if it is larger than 100 it is rounded down to 100.
| max_distance | double | The maximum distance in kilometers that a vehicle must be from latitude, longitude to be listed when using DISTANCE search mode.
| latitude | double | The latitude relative to the returned vehicles when using DISTANCE search mode.
| longitude | double | The longitude relative to the returned vehicles when using DISTANCE search mode.






#### ListVehiclesRequest.SearchMode

Available search modes when listing vehicles.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| ID | 0 | Return a paginated list of vehicles sorted by vehicle ID. |
| DISTANCE | 1 | Return all vehicles within max_distance of (latitude, longitude), sorted by the distance. |





### Response: ListVehiclesReply

Response payload for the list vehicles endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| vehicles | [Vehicle](public_resources.md#vehicle) | List of vehicles.
| next_id | string | ID of the next vehicle to return, if there are more results.








## Get vehicle

`GET /systems/<system_id>/vehicles/<vehicle_id>`

Get a vehicle in a system by its ID.

### Request: GetVehicleRequest

Request payload for the get vehicle endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system the vehicle is in.<br /><br />This is a URL parameter in the HTTP API.
| vehicle_id | string | ID of the vehicle.<br /><br />This is a URL parameter in the HTTP API.








### Response: [Vehicle](public_resources.md#vehicle)

## List shapes

`GET /systems/<system_id>/shapes`

List all shapes in a system.

### Request: ListShapesRequest

Request payload for the list shapes endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | System to list shapes for.
| only_return_specified_ids | bool | Deprecated: use `filter_by_id` instead.
| filter_by_id | bool | If true, only return shapes whose IDs are specified in the repeated `id` field.
| id | string | IDs to return if `filter_by_id` is set to true. It is an error to populate this field if `filter_by_id` is false.
| first_id | string | ID of the first shape to return. If not set, the shape with the smallest ID will be first.
| limit | int32 | Maximum number of shapes to return.








### Response: ListShapesReply

Response payload for the list shapes endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| shapes | [Shape](public_resources.md#shape) | Shapes that were listed.
| next_id | string | ID of the next shape to list, if there are more results.








## Get shape

`GET /systems/<system_id>/shapes/<shape_id>`

Get a shape in a system by its ID.

### Request: GetShapeRequest

Request payload for the get shape endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | System to get shape for.
| shape_id | string | ID of the shape to get.








### Response: [Shape](public_resources.md#shape)




