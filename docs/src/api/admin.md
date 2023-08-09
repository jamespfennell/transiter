


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
| force | bool | If true, a full feed update will be performed even if the download data is identical to the last update for this feed.








### Response type: UpdateFeedReply


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| feed_update | [FeedUpdate](admin.md#FeedUpdate) | 








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
| feed_config | [FeedConfig](admin.md#FeedConfig) | 
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
| type | string | The type of the feed. Allowable values are `GTFS_STATIC`, `GTFS_REALTIME` and `NYCT_SUBWAY_CSV`.<br /><br />The are possible future plans to support plugging in additional custom types at build time. This is why the field is a string and not an enum.
| parser | string | Deprecated: use `type` instead.
| gtfs_realtime_options | [GtfsRealtimeOptions](admin.md#GtfsRealtimeOptions) | Additional options GTFS realtime feeds.
| required_for_install | bool | Required for install specifies whether an update should be performed for this feed during system install. If true, an update is performed and if the update fails the installation fails.<br /><br />If unspecified, defaults to false for GTFS realtime feeds and true for all other types of feeds.
| scheduling_policy | [FeedConfig.SchedulingPolicy](admin.md#FeedConfig.SchedulingPolicy) | The scheduling policy to use for this feed.<br /><br />If unspecified, it takes the value `DEFAULT``.
| update_strategy | [FeedConfig.SchedulingPolicy](admin.md#FeedConfig.SchedulingPolicy) | Deprecated: use `scheduling_policy` instead.
| periodic_update_period_ms | int64 | For feeds with a `PERIODIC` scheduling policy, the update period.<br /><br />If unspecified, defaults to 5 seconds.
| update_period_s | double | Deprecated: use `periodic_update_period_ms` instead.
| daily_update_time | string | For feeds with a `DAILY` scheduling policy, the time of day in the form HH:MM at which to perform an update.<br /><br />If unspecified, defaults to 03:00 for the first feed in the system, 03:10 for the second feed, and so on. The idea of the default is to run at night when the system is either quiet or not running. The staggering is to avoid updates stepping on each other, and to spread out the load.
| daily_update_timezone | string | For feeds with a `DAILY` scheduling policy, the timezone for the time of day specified in the `daily_update_time`.<br /><br />If empty, a default is provided as follows. The scheduler lists the agencies for the system in order of ID and uses the first valid timezone it finds. Given the GTFS static specification this should always work. Moreover, all agencies should have the same timezone so listing in order of ID shouldn't matter. But in reality it may not work. If there is no valid agency timezones, the scheduler will log a warning and fall back to UTC.
| url | string | URL at which the feed can be downloaded using a HTTP GET request. Transiter does not currently support non-GET requests.
| request_timeout_ms | int64 | Timeout to enforce for the request to the feed URL. If not specified, defaults to 5 seconds.
| http_headers | [FeedConfig.HttpHeadersEntry](admin.md#FeedConfig.HttpHeadersEntry) | HTTP headers to send in the request.






#### FeedConfig.HttpHeadersEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 






#### FeedConfig.SchedulingPolicy

Transiter runs a background task called the scheduler which performs feed updates automatically.
A scheduling policy determines when the scheduler will perform feed updates for this feed.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| DEFAULT | 0 | Use the default policy, which is PERIODIC for GTFS realtime feeds and DAILY for all other feeds. |
| PERIODIC | 1 | Perform an update periodically, with the period specified in the `periodic_update_period_ms` field. |
| DAILY | 2 | Perform an update once a day, with the time of day specified in the `daily_update_time` field. |
| NONE | 3 | Don't perform updates in the scheduler. Updates can always be triggered manually using the admin API. |




### FeedUpdate

Description of a feed update operation.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| update_id | string | ID of the feed update. This is a randomly generated UUID. It can be used to find server logs for the update operation.
| feed_config | [FeedConfig](admin.md#FeedConfig) | The feed configuration that was used to perform the feed update.
| started_at_ms | int64 | Unix timestamp of when the update started.
| finished_at_ms | int64 | Unix timestamp of when the update finished. Only populated if the update is finished.
| total_latency_ms | int64 | 
| download_latency_ms | int64 | 
| parse_latency_ms | int64 | 
| database_latency_ms | int64 | 
| download_http_status_code | int32 | 
| status | [FeedUpdate.Status](admin.md#FeedUpdate.Status) | Status of the update.
| content_length | int32 | Number of bytes in the downloaded feed data. Only populated if the update successfully downloaded data.
| content_hash | string | Hash of the downloaded feed data. This is used to skip updates if the feed data hasn't changed. Only populated if the update successfully downloaded data.
| error_message | string | Error message of the update. Only populated if the update finished in an error






#### FeedUpdate.Status


	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN | 0 | Unknown status. |
| RUNNING | 1 | Feed update is in progress. Currently this status never appears in the admin API, but is
added in case Transiter support async feed updates in the future. |
| UPDATED | 2 | Finished successfully. |
| SKIPPED | 3 | The update was skipped because the downloaded data was identical to the data for the last successful update. |
| FAILED_DOWNLOAD_ERROR | 4 | Failed to download feed data. |
| FAILED_EMPTY_FEED | 5 | Feed data was empty. |
| FAILED_INVALID_FEED_CONFIG | 6 | The feed configuration is invalid. This typically indicates a bug in Transiter because
the feed configuration is validated when the system is being installed. |
| FAILED_PARSE_ERROR | 8 | Failed to parse the feed data.
This means the feed data was corrupted or otherwise invalid. |
| FAILED_UPDATE_ERROR | 9 | Failed to update the database using the new feed data.
This typically indicates a bug in Transiter or a transient error connecting to the database. |
| FAILED_INTERNAL_ERROR | 10 | An internal unspecified error occured. |
| FAILED_UNKNOWN_FEED_TYPE | 11 | The feed has an unknown type. |




### GtfsRealtimeOptions

Message describing additional options for the GTFS realtime feeds.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| extension | [GtfsRealtimeOptions.Extension](admin.md#GtfsRealtimeOptions.Extension) | 
| nyct_trips_options | [GtfsRealtimeOptions.NyctTripsOptions](admin.md#GtfsRealtimeOptions.NyctTripsOptions) | 
| nyct_alerts_options | [GtfsRealtimeOptions.NyctAlertsOptions](admin.md#GtfsRealtimeOptions.NyctAlertsOptions) | 
| reassign_stop_sequences | bool | If true, stop sequences in the GTFS realtime feed data are ignored, and alternative stop sequences are generated and assigned by Transiter. This setting is designed for buggy GTFS realtime feeds in which stop sequences (incorrectly) change between updates. In many cases Transiter is able to generate stop sequences that are correct and stable across updates.<br /><br />This should not be used for systems where a trip can call at the same stop multiple times.
| only_process_full_entities | bool | If true, only process entities in a feed if the message contains the full entity. This is useful for cases where there are multiple feeds for the same system, and some feeds contain only partial information about entities.






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








