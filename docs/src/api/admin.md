


# 

## Endpoints


## Get the config for a system

`GET /systems/<system_id>/config`

### Request type: GetSystemConfigRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | 








### Response type: [SystemConfig](admin.md#SystemConfig)

## Install or update a system

`PUT /systems/<system_id>`

Installs or updates the system based on the configuration provided in the
request payload.
If the system does not exist an install is performed; otherwise an update.

### Request type: InstallOrUpdateSystemRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system to install or update.
| system_config | [SystemConfig](admin.md#SystemConfig) | 
| yaml_config | [YamlConfig](admin.md#YamlConfig) | 
| install_only | bool | If true, do not perform an update if the system already exists.
| synchronous | bool | If false (the default), the system configuration is validated before the request finishes but databse updates are performed asynchronously. The status of the operation can be polled using GetSystem and inspecting the status field.<br /><br />If true, the install/update operation is perfomed synchronously in the request and in a single database transaction. In this case, if the operation fails there will no database artifacts. The problem is that installs can take a long time and the request may be cancelled before it completes e.g. by an intermediate proxy.








### Response type: InstallOrUpdateSystemReply


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | 
| system_config | [SystemConfig](admin.md#SystemConfig) | 








## Delete a system

`DELETE /systems/<system_id>`

Deletes the specified system.

### Request type: DeleteSystemRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | 








### Response type: DeleteSystemReply


	


No fields.







## Update a feed

`POST /systems/<system_id>/feeds/<feed_id>`

Triggers a feed update for the specified feed.

### Request type: UpdateFeedRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | 
| feed_id | string | 








### Response type: UpdateFeedReply


	


No fields.







## Get scheduler status

`GET /scheduler`

Gets the status of the scheduler.

### Request type: GetSchedulerStatusRequest


	


No fields.







### Response type: GetSchedulerStatusReply


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| feeds | [GetSchedulerStatusReply.Feed](admin.md#GetSchedulerStatusReply.Feed) | 






#### GetSchedulerStatusReply.Feed


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | 
| feed_id | string | 
| period | int64 | 
| last_successful_update | int64 | 
| last_finished_update | int64 | 
| currently_running | bool | 








## Reset scheduler

`POST /scheduler`

Performs a full restart of the scheduler, with all scheduler
  configurations retrieved fresh from the database.
In general this endpoint should never be needed;
  Transiter automatically restarts the scheduler when needed.
 The main usecase is when the Postgres configuration is manually
  updated and the scheduler needs to see the update.

### Request type: ResetSchedulerRequest


	


No fields.







### Response type: ResetSchedulerReply


	


No fields.










## Types


### FeedConfig


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| required_for_install | bool | 
| periodic_update_enabled | bool | 
| periodic_update_period_ms | int64 | 
| url | string | 
| http_timeout_ms | int64 | 
| http_headers | [FeedConfig.HttpHeadersEntry](admin.md#FeedConfig.HttpHeadersEntry) | 
| gtfs_static_parser | [FeedConfig.GtfsStaticParser](admin.md#FeedConfig.GtfsStaticParser) | 
| gtfs_realtime_parser | [FeedConfig.GtfsRealtimeParser](admin.md#FeedConfig.GtfsRealtimeParser) | 
| nyct_subway_csv_parser | [FeedConfig.NyctSubwayCsvParser](admin.md#FeedConfig.NyctSubwayCsvParser) | 






#### FeedConfig.GtfsRealtimeParser


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| no_extension | [FeedConfig.GtfsRealtimeParser.NoExtension](admin.md#FeedConfig.GtfsRealtimeParser.NoExtension) | 
| nyct_trips_extension | [FeedConfig.GtfsRealtimeParser.NyctTripsExtension](admin.md#FeedConfig.GtfsRealtimeParser.NyctTripsExtension) | 
| nyct_alerts_extension | [FeedConfig.GtfsRealtimeParser.NyctAlertsExtension](admin.md#FeedConfig.GtfsRealtimeParser.NyctAlertsExtension) | 






#### FeedConfig.GtfsRealtimeParser.NoExtension


	


No fields.





#### FeedConfig.GtfsRealtimeParser.NyctAlertsExtension


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| elevator_alerts_deduplication_policy | [FeedConfig.GtfsRealtimeParser.NyctAlertsExtension.ElevatorAlertsDeduplicationPolicy](admin.md#FeedConfig.GtfsRealtimeParser.NyctAlertsExtension.ElevatorAlertsDeduplicationPolicy) | 
| elevator_alerts_inform_using_station_ids | bool | 
| skip_timetabled_no_service_alerts | bool | 
| add_nyct_metadata | bool | 






#### FeedConfig.GtfsRealtimeParser.NyctAlertsExtension.ElevatorAlertsDeduplicationPolicy


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| NO_DEDUPLICATION | 0 |  |
| DEDUPLICATE_IN_STATION | 1 |  |
| DEDUPLICATE_IN_COMPLEX | 2 |  |



#### FeedConfig.GtfsRealtimeParser.NyctTripsExtension


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| filter_stale_unassigned_trips | bool | 






#### FeedConfig.GtfsStaticParser


	


No fields.





#### FeedConfig.HttpHeadersEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 






#### FeedConfig.NyctSubwayCsvParser


	


No fields.






### ServiceMapConfig


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | 
| static_source | [ServiceMapConfig.Static](admin.md#ServiceMapConfig.Static) | 
| realtime_source | [ServiceMapConfig.Realtime](admin.md#ServiceMapConfig.Realtime) | 
| threshold | double | 






#### ServiceMapConfig.Realtime


	


No fields.





#### ServiceMapConfig.Static


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| starts_earlier_than | int64 | 
| starts_later_than | int64 | 
| ends_earlier_than | int64 | 
| ends_later_than | int64 | 
| days | string | 







### SystemConfig


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| name | string | 
| feeds | [FeedConfig](admin.md#FeedConfig) | 
| service_maps | [ServiceMapConfig](admin.md#ServiceMapConfig) | 







### YamlConfig


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| url | string | A URL where the config can be retrieved from using a simple GET request. If the URL requires a more complex interaction (authentication, a different verb), the config should be retrieved outside of Transiter and provided using the content field.
| content | string | The text content of the yaml config.
| is_template | bool | Whether the config is a template. If true the config will first be processed using Go's template library.
| template_args | [YamlConfig.TemplateArgsEntry](admin.md#YamlConfig.TemplateArgsEntry) | Arguments to pass to Go's template library if the config is a template.<br /><br />In general all information should be in the config itself. The template args are intended for things like API keys which are secret and/or different for each installer of the system.






#### YamlConfig.TemplateArgsEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 








