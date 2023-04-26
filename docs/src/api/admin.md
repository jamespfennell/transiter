


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
If the system does not exist an install is performed; otherwise the system is updated.

This is an asynchronous operation.
The system configuration is validated before the request finishes
but database and feed updates are performed asynchronously. The status of the operation can
be determined by polling the GetSystem method and inspecting the status field.

### Request type: InstallOrUpdateSystemRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system to install or update.
| system_config | [SystemConfig](admin.md#SystemConfig) | 
| yaml_config | [TextConfig](admin.md#TextConfig) | TODO: TextConfig json_config = 4;
| install_only | bool | If true, do not perform an update if the system already exists.








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







## Garbage collect feed updates

`POST /gcfeedupdates`

Deletes feed updates that are older than a week, with the exception that
the most recent succesful update for each feed is always retained.

This method exists to avoid unbounded growth in the feed updates database table.
It is called periodically by the scheduler.

### Request type: GarbageCollectFeedUpdatesRequest


	


No fields.







### Response type: GarbageCollectFeedUpdatesReply


	


No fields.







## Get the current log level.

`GET /loglevel`

### Request type: GetLogLevelRequest


	


No fields.







### Response type: GetLogLevelReply


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| log_level | string | 








## Set the log level.

`PUT /loglevel`

### Request type: SetLogLevelRequest


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| log_level | string | 








### Response type: SetLogLevelReply


	


No fields.










## Types


### FeedConfig


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Identifier of this feed config. This must be unique within the system.
| required_for_install | bool | If true, an update of this feed will be performed during the system installation, and if the update fails the system installation will fail.
| update_strategy | [FeedConfig.UpdateStrategy](admin.md#FeedConfig.UpdateStrategy) | 
| update_period_s | double | 
| url | string | URL at which the feed can be downloaded using a HTTP GET request. Transiter does not currently support non-GET requests.
| request_timeout_ms | int64 | Timeout to enforce for the request to the feed URL. If not specified, defaults to 5 seconds.
| http_headers | [FeedConfig.HttpHeadersEntry](admin.md#FeedConfig.HttpHeadersEntry) | HTTP headers to send in the request.
| parser | string | The parser to parse the feed with. Current options are "GTFS_STATIC", "GTFS_REALTIME" and "NYCT_SUBWAY_CSV".<br /><br />The are future plans to support plugging in additional custom parsers at build time. This is why the field is a string and not an enum.
| gtfs_realtime_options | [GtfsRealtimeOptions](admin.md#GtfsRealtimeOptions) | Additional options for the GTFS realtime parser, if that is the parser in use.






#### FeedConfig.HttpHeadersEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 






#### FeedConfig.UpdateStrategy


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| NONE | 0 |  |
| PERIODIC | 1 |  |




### GtfsRealtimeOptions

Message describing options for the GTFS realtime parser.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| extension | [GtfsRealtimeOptions.Extension](admin.md#GtfsRealtimeOptions.Extension) | 
| nyct_trips_options | [GtfsRealtimeOptions.NyctTripsOptions](admin.md#GtfsRealtimeOptions.NyctTripsOptions) | 
| nyct_alerts_options | [GtfsRealtimeOptions.NyctAlertsOptions](admin.md#GtfsRealtimeOptions.NyctAlertsOptions) | 
| reassign_stop_sequences | bool | If true, stop sequences in the GTFS realtime feed data are ignored, and alternative stop sequences are generated and assigned by Transiter. This setting is designed for buggy GTFS realtime feeds in which stop sequences (incorrectly) change between updates. In many cases Transiter is able to generate stop sequences that are correct and stable across updates.<br /><br />This should not be used for systems where a trip can call at the same stop multiple times.






#### GtfsRealtimeOptions.Extension


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| NO_EXTENSION | 0 |  |
| NYCT_TRIPS | 1 |  |
| NYCT_ALERTS | 2 |  |
| NYCT_BUS_TRIPS | 3 |  |



#### GtfsRealtimeOptions.NyctAlertsOptions


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| elevator_alerts_deduplication_policy | [GtfsRealtimeOptions.NyctAlertsOptions.ElevatorAlertsDeduplicationPolicy](admin.md#GtfsRealtimeOptions.NyctAlertsOptions.ElevatorAlertsDeduplicationPolicy) | 
| elevator_alerts_inform_using_station_ids | bool | 
| skip_timetabled_no_service_alerts | bool | 
| add_nyct_metadata | bool | 






#### GtfsRealtimeOptions.NyctAlertsOptions.ElevatorAlertsDeduplicationPolicy


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| NO_DEDUPLICATION | 0 |  |
| DEDUPLICATE_IN_STATION | 1 |  |
| DEDUPLICATE_IN_COMPLEX | 2 |  |



#### GtfsRealtimeOptions.NyctTripsOptions


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| filter_stale_unassigned_trips | bool | 
| preserve_m_train_platforms_in_bushwick | bool | 







### ServiceMapConfig

Description of the configuration for a collection of service maps.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Identifier of this service maps config. This must be unique within the system.
| source | [ServiceMapConfig.Source](admin.md#ServiceMapConfig.Source) | Source of the service maps built using this config.
| threshold | double | The threshold setting is used to exclude one-off trip schedules from service maps. When calculating a service map, all trips are bucketed based on their schedule. If the threshold is 0.2, trips are only included if the corresponding bucket contains at least 20% of the trips. In particular, a one-off trip whose bucket only contains itself will be excluded if there are many other trips.<br /><br />Note that a trip's schedule is reversed if needed based on the direction ID.
| static_options | [ServiceMapConfig.StaticOptions](admin.md#ServiceMapConfig.StaticOptions) | Additional options relevent for static service maps only.






#### ServiceMapConfig.Source

Source describes the possible sources for service maps.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATIC | 0 | Build the service maps using the GTFS static data. |
| REALTIME | 1 | Build the service maps using the GTFS realtime data. |



#### ServiceMapConfig.StaticOptions

Description of options relevent for static service maps only.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| starts_earlier_than | double | If specified, only include trips that start earlier than this time. The time is specified as a number of hours after midnight; i.e., 2:30am is '2.5'.
| starts_later_than | double | If specified, only include trips that start later than this time.
| ends_earlier_than | double | If specified, only include trips that end earlier than this time.
| ends_later_than | double | If specified, only include trips that end later than this time.
| days | string | If specified, only include trips which run on at least one of the provided days. If left empty, no trip filtering is provided.







### SystemConfig

Configuration for a system.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| name | string | Name of the system.
| feeds | [FeedConfig](admin.md#FeedConfig) | Configuration for the system's feeds.
| service_maps | [ServiceMapConfig](admin.md#ServiceMapConfig) | Configuration for the system's service maps.







### TextConfig

TextConfig contains a Transiter system configuration in non-proto format
(e.g. YAML or JSON).
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| url | string | A URL where the config can be retrieved from using a simple GET request. If the URL requires a more complex interaction (authentication, a different HTTP verb), the config should be retrieved outside of Transiter and provided in the content field.
| content | string | The text content of the config.
| is_template | bool | Whether the config is a template. If true the config will first be processed using Go's template library.
| template_args | [TextConfig.TemplateArgsEntry](admin.md#TextConfig.TemplateArgsEntry) | Arguments to pass to Go's template library if the config is a template.<br /><br />In general as much information as possible should be in the config itself. The template args are intended for things like API keys which are secret and/or different for each person that installs the system.






#### TextConfig.TemplateArgsEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 








