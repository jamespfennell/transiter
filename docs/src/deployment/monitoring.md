# Monitoring using Prometheus

When running Transiter, it is critical that successful feed updates are occurring regularly.
Otherwise, the data in the Transiter instance will be stale.
In order to monitor the feed update process, Transiter exports metrics in Prometheus format on the `/metrics`
    endpoint.

There are four metrics exported.
For architectural reasons, these metrics are ultimately managed in the scheduler process.
If that process is not running, metrics will be unavailable.

## TRANSITER_NUM_UPDATES

This metric has four labels: `system_id`, `feed_id`, `status` (either `FAILURE` or `SUCCESS`), and `result`.
For each label, the corresponding time series reports the number of updates that have finished for that feed
    and with that status

Generally one will be interested in the `SUCCESS` case.
For this case there are two possible results: `UPDATED` and `NOT_NEEDED`.
The latter indicates that Transiter performed the feed update, 
    but that the data it retrieved from the transit agency was identical to the last successful update.
In this case the rest of the feed update process is skipped.
If `NOT_NEEDED` is seen consecutively for a long time, it indicates that the transit agency is not provided updated data.
This may be a failure case, even though the status is `SUCCESS`.
Or, it may not be a failure case if it's nighttime, and the transit agency not running any services.


## TRANSITER_LAST_UPDATE

This metric has the same four labels as the last.
For each label, the corresponding time series reports the timestamp when the last update for that feed and
with that status occurred.


## TRANSITER_SUCCESSFUL_UPDATE_LATENCY

This metric has two labels: `system_id` and `feed_id`.
The metric reports the number of seconds between the last two feed updates with status `SUCCESS` and result `UPDATED`.
Over time, the metric is an accurate measure of how often data from that feed is being updated.

This metric is a good candidate for alerting because if is large, it directly indicates stale data.
There is a catch, though: if the reason feed updates are not occurring is because of internal problems with Transiter
(for example, RabbitMQ is down), the most recent value of the metric will stay constant and not indicate a problem.
Conversely, the `TRANSITER_NUM_UPDATES` metric will still catch this case: if that metric remains constant for a long
    time, it indicates no updates are happening.


## TRANSITER_NUM_ENTITIES

This metric reports the number of entities (trips, alerts, routes, etc.)
that are in the system, by feed.
It has three labels: `system_id`, `feed_id` and `entity_type`.
