

# Admin API

The admin API is a private API used to manage a running Transiter instance.
It should generally be inaccessible from the internet as the API can be used to e.g.
delete all of the transit systems that are installed.

## Endpoints


## Get the config for a system

`GET /systems/<system_id>/config`

### Request: GetSystemConfigRequest

Request payload for the get system config endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system whose config is to be retrieved.








### Response: [SystemConfig](admin.md#systemconfig)

## Install or update a system

`PUT /systems/<system_id>`

Installs or updates the system based on the configuration provided in the
request payload.
If the system does not exist an install is performed; otherwise the system is updated.

This is an asynchronous operation.
The system configuration is validated before the request finishes
but database and feed updates are performed asynchronously. The status of the operation can
be determined by polling the [GetSystem endpoint](public_endpoints.md#get-system)
and inspecting the status field of the system.

### Request: InstallOrUpdateSystemRequest

Request payload for the install or update system endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system to install or update.
| system_config | [SystemConfig](admin.md#systemconfig) | Config for the system, in the form or a protobuf message.
| yaml_config | [YamlConfig](admin.md#yamlconfig) | Config for the system, in the form of a YAML file.
| install_only | bool | If true, do not perform an update if the system already exists.








### Response: InstallOrUpdateSystemReply

Response payload for the install of update system endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system that was installed.
| system_config | [SystemConfig](admin.md#systemconfig) | System configuration that was used for the install. If the configuration was provided as a YAML file or a YAML template, the value here represents the fully parsed and expanded configuration.








## Delete a system

`DELETE /systems/<system_id>`

Deletes the specified system.

### Request: DeleteSystemRequest

Request payload for the delete system endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system to delete.








### Response: DeleteSystemReply

Response payload for the delete system endpoint.
	


No fields.







## Update a feed

`POST /systems/<system_id>/feeds/<feed_id>`

Triggers a feed update for the specified feed.

### Request: UpdateFeedRequest

Request payload for the update feed endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system containing the feed to update.
| feed_id | string | ID of the feed to update.
| force | bool | If true, a full feed update will be performed even if the downloaded data is identical to the last update for this feed.








### Response: UpdateFeedReply

Response payload for the update feed endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| feed_update | [FeedUpdate](admin.md#feedupdate) | Information about the feed update that was performed.








## Get scheduler status

`GET /scheduler`

Gets the status of the scheduler.

### Request: GetSchedulerStatusRequest

Request payload for the get scheduler status endpoint.
	


No fields.







### Response: GetSchedulerStatusReply

Response payload for the get scheduler status endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| feeds | [GetSchedulerStatusReply.FeedStatus](admin.md#getschedulerstatusreplyfeedstatus) | Status for all feeds being updated by the scheduler.






#### GetSchedulerStatusReply.FeedStatus

Description of the status of one feed.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| system_id | string | ID of the system this feed belongs to.
| feed_config | [FeedConfig](admin.md#feedconfig) | Configuration of the feed as used by the scheduler. If Postgres is manually updated to change the feed configuration, this may be different what's in Postgres. The scheduler needs to be updated in this case. In general, however, the feed config here will match what's in Postgres.
| last_successful_update | int64 | Unix timestamp of the last successful feed update.
| last_finished_update | int64 | Unix timestamp of the last finished update.
| currently_running | bool | Whether a feed update for this feed is currently running.








## Reset scheduler

`POST /scheduler`

Performs a full restart of the scheduler, with all scheduler
  configurations retrieved fresh from the database.
In general this endpoint should never be needed;
  Transiter automatically restarts the scheduler when needed.
 The main use-case is when the Postgres configuration is manually
  updated and the scheduler needs to see the update.

### Request: ResetSchedulerRequest

Request payload for the reset scheduler endpoint.
	


No fields.







### Response: ResetSchedulerReply

Response payload for the reset scheduler endpoint.
	


No fields.







## Get the current log level.

`GET /loglevel`

### Request: GetLogLevelRequest

Request payload for the get log level endpoint.
	


No fields.







### Response: GetLogLevelReply

Response payload for the get log level endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| log_level | [LogLevel](admin.md#loglevel) | Current log level.








## Set the log level.

`PUT /loglevel`

### Request: SetLogLevelRequest

Request payload for the set log level endpoint.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| log_level | [LogLevel](admin.md#loglevel) | New log level.








### Response: SetLogLevelReply

Response payload for the set log level endpoint.
	


No fields.










## Types


### FeedConfig

Configuration for a transit system data feed.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Identifier of this feed config. This must be unique within the system.
| type | string | The type of the feed. Allowable values are `GTFS_STATIC`, `GTFS_REALTIME` and `NYCT_SUBWAY_CSV`.<br /><br />The are possible future plans to support plugging in additional custom types at build time. This is why the field is a string and not an enum.
| parser | string | Deprecated: use `type` instead.
| gtfs_realtime_options | [GtfsRealtimeOptions](admin.md#gtfsrealtimeoptions) | Additional options GTFS realtime feeds.
| required_for_install | bool | Required for install specifies whether an update should be performed for this feed during system install. If true, an update is performed and if the update fails the installation fails.<br /><br />If unspecified, defaults to false for GTFS realtime feeds and true for all other types of feeds.
| scheduling_policy | [FeedConfig.SchedulingPolicy](admin.md#feedconfigschedulingpolicy) | The scheduling policy to use for this feed.<br /><br />If unspecified, it takes the value `DEFAULT``.
| update_strategy | [FeedConfig.SchedulingPolicy](admin.md#feedconfigschedulingpolicy) | Deprecated: use `scheduling_policy` instead.
| periodic_update_period_ms | int64 | For feeds with a `PERIODIC` scheduling policy, the update period.<br /><br />If unspecified, defaults to 5 seconds.
| update_period_s | double | Deprecated: use `periodic_update_period_ms` instead.
| daily_update_time | string | For feeds with a `DAILY` scheduling policy, the time of day in the form HH:MM at which to perform an update.<br /><br />If unspecified, defaults to 03:00 for the first feed in the system, 03:10 for the second feed, and so on. The idea of the default is to run at night when the system is either quiet or not running. The staggering is to avoid updates stepping on each other, and to spread out the load.
| daily_update_timezone | string | For feeds with a `DAILY` scheduling policy, the timezone for the time of day specified in the `daily_update_time`.<br /><br />If empty, a default is provided as follows. The scheduler lists the agencies for the system in order of ID and uses the first valid timezone it finds. Given the GTFS static specification this should always work. Moreover, all agencies should have the same timezone so listing in order of ID shouldn't matter. But in reality it may not work. If there is no valid agency timezones, the scheduler will log a warning and fall back to UTC.
| url | string | URL at which the feed can be downloaded using a HTTP GET request. Transiter does not currently support non-GET requests.
| request_timeout_ms | int64 | Timeout to enforce for the request to the feed URL. If not specified, defaults to 5 seconds.
| http_headers | [FeedConfig.HttpHeadersEntry](admin.md#feedconfighttpheadersentry) | HTTP headers to send in the request.
| nyct_subway_options | [FeedConfig.NyctSubwayOptions](admin.md#feedconfignyctsubwayoptions) | Additional options for NYCT Subway feeds.






#### FeedConfig.HttpHeadersEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 






#### FeedConfig.NyctSubwayOptions

Additional options for NYCT Subway CSV feeds.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| use_accessibility_info | bool | If true, infer the 'wheelchair_boarding' field from this feed.<br /><br />Historically, this information is not set in the NYC Subway GTFS feed, but is included in the extended NYCT_SUBWAY_CSV feed.<br /><br />To use the data from the CSV feed, set thie field to true on that feed and false on the GTFS static feed. If this field is not set on either feed, the GTFS static feed will be used.<br /><br />Avoid setting this field to true on both feeds, as this will result in non-deterministic behavior, since feed updates are not guaranteed to be ordered after initial system installation.






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
| feed_config | [FeedConfig](admin.md#feedconfig) | The feed configuration that was used to perform the feed update.
| started_at_ms | int64 | Unix timestamp of when the update started.
| finished_at_ms | int64 | Unix timestamp of when the update finished. Only populated if the update is finished.
| total_latency_ms | int64 | Total latency of the feed update, in milliseconds.
| download_latency_ms | int64 | Latency of the HTTP request, in milliseconds.
| parse_latency_ms | int64 | Latency of parsing the downloaded data, in milliseconds.
| database_latency_ms | int64 | Latency of updating the database with the parsed data, in milliseconds.
| download_http_status_code | int32 | Status code returned by the HTTP request.
| status | [FeedUpdate.Status](admin.md#feedupdatestatus) | Status of the update.
| content_length | int32 | Number of bytes in the downloaded feed data. Only populated if the update successfully downloaded data.
| content_hash | string | Hash of the downloaded feed data. This is used to skip updates if the feed data hasn't changed. Only populated if the update successfully downloaded data.
| error_message | string | Error message of the update. Only populated if the update finished in an error






#### FeedUpdate.Status

Status of a feed update.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| UNKNOWN | 0 | Unknown status. |
| RUNNING | 1 | Feed update is in progress. Currently this status never appears in the admin API, but is added in case Transiter support async feed updates in the future. |
| UPDATED | 2 | Finished successfully. |
| SKIPPED | 3 | The update was skipped because the downloaded data was identical to the data for the last successful update. |
| FAILED_DOWNLOAD_ERROR | 4 | Failed to download feed data. |
| FAILED_EMPTY_FEED | 5 | Feed data was empty. |
| FAILED_INVALID_FEED_CONFIG | 6 | The feed configuration is invalid. This typically indicates a bug in Transiter because the feed configuration is validated when the system is being installed. |
| FAILED_PARSE_ERROR | 8 | Failed to parse the feed data. This means the feed data was corrupted or otherwise invalid. |
| FAILED_UPDATE_ERROR | 9 | Failed to update the database using the new feed data. This typically indicates a bug in Transiter or a transient error connecting to the database. |
| FAILED_INTERNAL_ERROR | 10 | An internal unspecified error occurred. |
| FAILED_UNKNOWN_FEED_TYPE | 11 | The feed has an unknown type. |




### GtfsRealtimeOptions

Message describing additional options for the GTFS realtime feeds.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| extension | [GtfsRealtimeOptions.Extension](admin.md#gtfsrealtimeoptionsextension) | GTFS realtime extension to use.
| nyct_trips_options | [GtfsRealtimeOptions.NyctTripsOptions](admin.md#gtfsrealtimeoptionsnycttripsoptions) | Options for the NYCT trips extension. Ignored if the extension field is not `NYCT_TRIPS`.
| nyct_alerts_options | [GtfsRealtimeOptions.NyctAlertsOptions](admin.md#gtfsrealtimeoptionsnyctalertsoptions) | Options for the NYCT alerts extension. Ignored if the extension field is not `NYCT_ALERTS`.
| reassign_stop_sequences | bool | If true, stop sequences in the GTFS realtime feed data are ignored, and alternative stop sequences are generated and assigned by Transiter. This setting is designed for buggy GTFS realtime feeds in which stop sequences (incorrectly) change between updates. In many cases Transiter is able to generate stop sequences that are correct and stable across updates.<br /><br />This should not be used for systems where a trip can call at the same stop multiple times.






#### GtfsRealtimeOptions.Extension

Supported GTFS realtime extensions.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| NO_EXTENSION | 0 |  |
| NYCT_TRIPS | 1 |  |
| NYCT_ALERTS | 2 |  |



#### GtfsRealtimeOptions.NyctAlertsOptions

Options for the NYCT alerts extension.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| elevator_alerts_deduplication_policy | [GtfsRealtimeOptions.NyctAlertsOptions.ElevatorAlertsDeduplicationPolicy](admin.md#gtfsrealtimeoptionsnyctalertsoptionselevatoralertsdeduplicationpolicy) | Deduplication policy for elevator alerts.
| elevator_alerts_inform_using_station_ids | bool | If true, the stop IDs in alerts will always be converted to point to stations. E.g., if the alert is for the stop F20N (northbound F platform at Bergen St.) it will be transformed to be for stop F20 (Bergen St. station).
| skip_timetabled_no_service_alerts | bool | When there are no trains running for a route due to the standard timetable (e.g., there are no C trains overnight), the MTA publishes an alert. Arguably this is not really an alert because this information is already in the timetable. If true, these alerts are skipped.
| add_nyct_metadata | bool | The NYCT alerts extension contains many fields like "time alert created at" that don't map to fields in the standard GTFS realtime protobuf. If true, these fields are put in a json blob and included as an alert description.






#### GtfsRealtimeOptions.NyctAlertsOptions.ElevatorAlertsDeduplicationPolicy

Available deduplication policies for elevator alerts.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| NO_DEDUPLICATION | 0 |  |
| DEDUPLICATE_IN_STATION | 1 |  |
| DEDUPLICATE_IN_COMPLEX | 2 |  |



#### GtfsRealtimeOptions.NyctTripsOptions

Options for the NYCT trips extension.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| filter_stale_unassigned_trips | bool | Filter out trips which are scheduled to run in the past but have no assigned trip and haven't started.
| preserve_m_train_platforms_in_bushwick | bool | The raw MTA data has a bug in which the M train platforms are reported incorrectly for stations in Williamsburg and Bushwick that the M shares with the J train. In the raw data, M trains going towards the Williamsburg bridge stop at M11N, but J trains going towards the bridge stop at M11S. By default this extension fixes these platforms for the M train, so M11N becomes M11S. This fix can be disabled by setting this option to true.







### LogLevel

Supported log levels in Transiter.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| INFO | 0 |  |
| DEBUG | 1 |  |
| WARN | 2 |  |
| ERROR | 3 |  |




### ServiceMapConfig

Description of the configuration for a collection of service maps.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| id | string | Identifier of this service maps config. This must be unique within the system.
| source | [ServiceMapConfig.Source](admin.md#servicemapconfigsource) | Source of the service maps built using this config.
| threshold | double | The threshold setting is used to exclude one-off trip schedules from service maps. When calculating a service map, all trips are bucketed based on their schedule. If the threshold is 0.2, trips are only included if the corresponding bucket contains at least 20% of the trips. In particular, a one-off trip whose bucket only contains itself will be excluded if there are many other trips.<br /><br />Note that a trip's schedule is reversed if needed based on the direction ID.
| static_options | [ServiceMapConfig.StaticOptions](admin.md#servicemapconfigstaticoptions) | Additional options relevant for static service maps only.






#### ServiceMapConfig.Source

Source describes the possible sources for service maps.
	



| Name | Number | Description |
| ---- | ------ | ----------- |
| STATIC | 0 | Build the service maps using the GTFS static data. |
| REALTIME | 1 | Build the service maps using the GTFS realtime data. |



#### ServiceMapConfig.StaticOptions

Description of options relevant for static service maps only.
	


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
| feeds | [FeedConfig](admin.md#feedconfig) | Configuration for the system's feeds.
| service_maps | [ServiceMapConfig](admin.md#servicemapconfig) | Configuration for the system's service maps.







### YamlConfig

YamlConfig contains a Transiter system configuration in YAML format.
	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| content | string | The YAML content.
| is_template | bool | Whether the config is a template. If true the config will first be processed using Go's template library.
| template_args | [YamlConfig.TemplateArgsEntry](admin.md#yamlconfigtemplateargsentry) | Arguments to pass to Go's template library if the config is a template.<br /><br />In general as much information as possible should be in the config itself. The template args are intended for things like API keys which are secret and/or different for each person that installs the system.






#### YamlConfig.TemplateArgsEntry


	


| Field | Type |  Description |
| ----- | ---- | ----------- |
| key | string | 
| value | string | 








