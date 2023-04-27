import time

import requests

from . import gtfsrealtimegenerator


def test_periodic_update(system_id, install_system_1, transiter_host, source_server):

    __, realtime_feed_url = install_system_1(system_id, "0.5")

    # Wait for a successful update
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(0, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    t = _wait_for_successful_update(system_id, transiter_host, None)

    # Wait for a skipped update
    t = _wait_for_skipped_update(system_id, transiter_host, t)

    # Empty feed
    source_server.put(realtime_feed_url, "")
    t = _wait_for_failed_update(system_id, transiter_host, t)

    # Wait for a successful update
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(100, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    t = _wait_for_successful_update(system_id, transiter_host, t)

    # Invalid feed content
    source_server.put(realtime_feed_url, "not a valid GTFS realtime message")
    t = _wait_for_failed_update(system_id, transiter_host, t)

def _wait_for_successful_update(system_id, transiter_host, lower_bound):
    actual_result = None
    for __ in range(40):
        time.sleep(0.1)
        feed = requests.get(
            transiter_host + "/systems/" + system_id + "/feeds/GtfsRealtimeFeed"
        ).json()
        print(feed)
        last_successful_update = feed.get("lastSuccessfulUpdateMs")
        if last_successful_update is None:
            continue
        if lower_bound is None or lower_bound < last_successful_update:
            return last_successful_update
    assert False, "successful update never appeared"

def _wait_for_skipped_update(system_id, transiter_host, lower_bound):
    actual_result = None
    for __ in range(40):
        time.sleep(0.1)
        feed = requests.get(
            transiter_host + "/systems/" + system_id + "/feeds/GtfsRealtimeFeed"
        ).json()
        print(feed)
        last_skipped_update = feed.get("lastSkippedUpdateMs")
        if last_skipped_update is None:
            continue
        if lower_bound < last_skipped_update:
            return last_skipped_update
    assert False, "skipped update never appeared"

def _wait_for_failed_update(system_id, transiter_host, lower_bound):
    actual_result = None
    for __ in range(40):
        time.sleep(0.1)
        feed = requests.get(
            transiter_host + "/systems/" + system_id + "/feeds/GtfsRealtimeFeed"
        ).json()
        print(feed)
        last_failed_update = feed.get("lastFailedUpdateMs")
        if last_failed_update is None:
            continue
        if lower_bound < last_failed_update:
            return last_failed_update
    assert False, "failed update never appeared"
