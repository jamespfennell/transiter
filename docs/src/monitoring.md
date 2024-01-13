# Monitoring Transiter

Transiter includes Prometheus metrics for monitoring a running Transiter deployment.
If you are running Transiter,
    the main thing you are likely interested in is how feed updates are performing.
If feed updates are failing, the data being served by your Transiter instance will be stale.

This page describes the most interesting metrics.
All of the metrics are defined [in this Go source file](https://github.com/jamespfennell/transiter/blob/master/internal/monitoring/monitoring.go)
If you have an idea for a new metric, please file an issue or create a PR.

## Feed update metrics

All of these metrics contain at least 3 labels: `system_id`, `feed_id` and `feed_type`.
The feed type (e.g. `GTFS_STATIC`, `GTFS_REALTIME`, etc.)
    can be useful for creating graphs that just target realtime feeds.

### Last completed feed update

The gauge metric `transiter_feed_update_last_completed` reports the Unix timestamp of
    when the last feed update completed.
This is partitioned by a label `result` which can be either `SUCCESS`, `FAILURE` or `SKIPPED`.
Feed updates are skipped when the transit agency's data hasn't changed.

**Example graphs**

Number of seconds since each realtime feed last successfully updated:

```
time() - (max by (system_id, feed_id) (transiter_feed_update_last_completed{feed_type="GTFS_REALTIME", result!="FAILED"})) / 1000
```

Number of seconds since new data was obtained for each realtime feed:

```
time() - (max by (system_id, feed_id) (transiter_feed_update_last_completed{feed_type="GTFS_REALTIME", result="SUCCESS"})) / 1000
```

### Number of feed updates, partitioned by status

The counter metric `transiter_feed_update_count` reports the number of feed updates.
It has a `status` label which reports the status of the feed update.
This can be `SUCCESS`, `SKIPPED` or another status like `FAILED_DOWNLOAD_ERROR` which denotes a specific kind of error.

**Example graph**: number of failed feed updates per minute:

```
rate(transiter_feed_update_count{status!="UPDATED", status!="SKIPPED"}[5m]) * 60
```

### Latency of successful feed updates

The distribution metric `transiter_feed_update_success_latency` reports how long successful feed updates took.
Like all Go Prometheus distribution metrics it has two counters associated with it:

- `transiter_feed_update_success_latency_count`:
    number of data points counter,
    which counts the number of successful feed updates.
- `transiter_feed_update_success_latency_sum`:
    sum of all latencies for all successful feed updates.

**Example graphs**

Successful feed updates per minute:
```
rate(transiter_feed_update_success_latency_count[5m]) * 60
```

Average update time over a 5 minute window:
```
rate(transiter_feed_update_success_latency_sum[5m]) / rate(transiter_feed_update_success_latency_count[5m])
```

## API response metric

There is currently one distribution metric `transiter_public_request_latency_bucket`
    which reports the latency of public API responses.
Note this latency only counts the time Transiter takes to handle the request.
It does not count how long it takes the request to reach the server,
    transit through any reverse proxies,
    be parsed by the Go HTTP package etc.

**Example graphs**

50th, 90th and 95th percentile response times for the "get stop" endpoint:

```
histogram_quantile(0.5, sum(rate(transiter_public_request_latency_bucket{method_name="GetStop"}[5m])) by (le))
```

```
histogram_quantile(0.9, sum(rate(transiter_public_request_latency_bucket{method_name="GetStop"}[5m])) by (le))
```

```
histogram_quantile(0.95, sum(rate(transiter_public_request_latency_bucket{method_name="GetStop"}[5m])) by (le))
```

Requests per second by method:

```
rate(transiter_public_request_latency_count[1m])
```

Request errors per minute:

```
rate(transiter_public_request_latency_count{response_status != "OK"}[10m]) * 60
```