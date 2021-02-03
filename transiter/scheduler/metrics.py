import logging
import typing
import time

import prometheus_client as prometheus

from transiter.services import feedservice
from transiter.db import models

logger = logging.getLogger(__name__)


# These are the names of the Prometheus metrics
PROMETHEUS_NUM_UPDATES = "transiter_num_updates"
PROMETHEUS_LAST_UPDATE = "transiter_last_update"
PROMETHEUS_SUCCESSFUL_UPDATE_LATENCY = "transiter_successful_update_latency"
PROMETHEUS_NUM_ENTITIES = "transiter_num_entities"


class MetricsPopulator:
    def __init__(self):
        self._feed_pk_to_system_id_and_feed_id = {}
        self._feed_pk_to_successful_update_data: typing.Dict[
            int, typing.Tuple[float, float]
        ] = {}

        self._num_updates = prometheus.Counter(
            PROMETHEUS_NUM_UPDATES,
            "Number of feed updates of a given feed, status and result",
            ["system_id", "feed_id", "status", "result"],
        )
        self._last_update = prometheus.Gauge(
            PROMETHEUS_LAST_UPDATE,
            "Time since the last update of a given feed, status and result",
            ["system_id", "feed_id", "status", "result"],
        )
        self._num_entities = prometheus.Gauge(
            PROMETHEUS_NUM_ENTITIES,
            "Number of entities of a given type present from a given feed",
            ["system_id", "feed_id", "entity_type"],
        )
        self._update_latency = prometheus.Gauge(
            PROMETHEUS_SUCCESSFUL_UPDATE_LATENCY,
            "Number of seconds between successful updates of a feed",
            ["system_id", "feed_id"],
        )

    def refresh(self):
        self._feed_pk_to_system_id_and_feed_id = (
            feedservice.get_feed_pk_to_system_id_and_feed_id_map()
        )

    def report(self, blob):
        if blob is None:
            return "expected JSON payload"

        try:
            feed_pk = int(blob["feed_pk"])
        except KeyError:
            return "missing field 'feed_pk'"
        except ValueError:
            return "could not parse feed_pk='{}' as an integer".format(blob["feed_pk"])
        system_id, feed_id = self._feed_pk_to_system_id_and_feed_id.get(
            feed_pk, (None, None)
        )
        if system_id is None:
            return "unknown feed_pk={}".format(feed_pk)

        if "result" not in blob:
            return "missing field 'result'"
        try:
            result = models.FeedUpdate.Result[blob["result"]]
        except KeyError:
            return "could not interpret result='{}' as a valid result value".format(
                blob["result"]
            )

        if "status" not in blob:
            return "missing field 'status'"
        try:
            status = models.FeedUpdate.Status[blob["status"]]
        except KeyError:
            return "could not interpret status='{}' as a valid status value".format(
                blob["status"]
            )

        self._num_updates.labels(
            system_id=system_id,
            feed_id=feed_id,
            status=status.name,
            result=result.name,
        ).inc()
        self._last_update.labels(
            system_id=system_id, feed_id=feed_id, status=status.name, result=result,
        ).set_to_current_time()
        self._report_latency(feed_pk, result, system_id, feed_id)
        for entity_type, count in blob.get("entity_type_to_count", {}).items():
            # TODO: verify each entity_type is valid or skip?
            self._num_entities.labels(
                system_id=system_id, feed_id=feed_id, entity_type=entity_type
            ).set(int(count))

        logger.debug(
            "Reporting %s/%s result=%s status=%s", system_id, feed_id, result, status,
        )
        return None

    def _report_latency(self, feed_pk, result, system_id, feed_id):
        # TODO: get the update time from the callback?
        update_time, latency = self._feed_pk_to_successful_update_data.get(
            feed_pk, (None, None)
        )
        if update_time is None:
            if result == models.FeedUpdate.Result.UPDATED:
                self._feed_pk_to_successful_update_data[feed_pk] = (
                    time.time(),
                    0,
                )
            # If there has been no successful update yet, we don't report latency
            return
        if result == models.FeedUpdate.Result.UPDATED:
            new_latency = time.time() - update_time
            new_time = time.time()
        else:
            new_time = update_time
            # We need to take the max of the time since the last update and the previously reported latency
            # Because otherwise NOT_NEEDED updates routinely mess it up
            new_latency = max(time.time() - update_time, latency)
        self._feed_pk_to_successful_update_data[feed_pk] = (
            new_time,
            new_latency,
        )
        self._update_latency.labels(system_id=system_id, feed_id=feed_id,).set(
            new_latency
        )
