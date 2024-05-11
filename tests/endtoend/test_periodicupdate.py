import time
from . import shared
from . import client
from . import gtfs_realtime_pb2 as gtfs_rt


def test_periodic_update(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
    source_server,
):
    __, realtime_feed_url = install_system(
        system_id, shared.GTFS_STATIC_DEFAULT_TXTAR, realtime_update_period=0.1
    )

    # Wait for a successful update
    feed_content = gtfs_rt.FeedMessage(
        header=gtfs_rt.FeedHeader(gtfs_realtime_version="2.0", timestamp=0)
    )
    source_server.put(realtime_feed_url, feed_content.SerializeToString())
    t = _wait_for_update(system_id, transiter_client, "lastSuccessfulUpdateMs", None)

    # Wait for a skipped update
    t = _wait_for_update(system_id, transiter_client, "lastSkippedUpdateMs", t)

    # Empty feed
    source_server.put(realtime_feed_url, "")
    t = _wait_for_update(system_id, transiter_client, "lastFailedUpdateMs", t)

    # Wait for a successful update
    feed_content = gtfs_rt.FeedMessage(
        header=gtfs_rt.FeedHeader(gtfs_realtime_version="2.0", timestamp=100)
    )
    source_server.put(realtime_feed_url, feed_content.SerializeToString())
    t = _wait_for_update(system_id, transiter_client, "lastSuccessfulUpdateMs", t)

    # Invalid feed content
    source_server.put(realtime_feed_url, "not a valid GTFS realtime message")
    t = _wait_for_update(system_id, transiter_client, "lastFailedUpdateMs", t)


def _wait_for_update(
    system_id, transiter_client: client.TransiterClient, feed_field: str, lower_bound
):
    for __ in range(40):
        time.sleep(0.01)
        feed = transiter_client.get_feed(system_id, shared.GTFS_REALTIME_FEED_ID)
        last_relevant_update = getattr(feed, feed_field)
        if last_relevant_update is None:
            continue
        if lower_bound is None or lower_bound < last_relevant_update:
            return int(last_relevant_update)
    assert False, "update never appeared"
