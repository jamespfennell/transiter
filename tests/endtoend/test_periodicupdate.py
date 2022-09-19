import time

import requests

from . import gtfsrealtimegenerator


def test_periodic_update(system_id, install_system_1, transiter_host, source_server):

    __, realtime_feed_url = install_system_1(system_id, "0.5s")
    source_server.put(realtime_feed_url, "")

    # Check that the realtime feed is initially failing
    _wait_for_update(system_id, transiter_host, "EMPTY_FEED")

    # Then, check for a successful update (with the right hash?)
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(0, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    _wait_for_update(system_id, transiter_host, "UPDATED")

    # Then, check for a redundant update
    _wait_for_update(system_id, transiter_host, "NOT_NEEDED")

    # Empty feed
    source_server.put(realtime_feed_url, "")
    _wait_for_update(system_id, transiter_host, "EMPTY_FEED")

    # Invalid feed content
    source_server.put(realtime_feed_url, "not a valid GTFS realtime message")
    _wait_for_update(system_id, transiter_host, "PARSE_ERROR")

    # Finally, a new update
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(100, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    _wait_for_update(system_id, transiter_host, "UPDATED")

    # Download error (here a simulated 404)
    #
    # We put this last because deleting the resource from the source server kind of messes it up
    source_server.delete(realtime_feed_url)
    _wait_for_update(system_id, transiter_host, "DOWNLOAD_ERROR")


def _wait_for_update(system_id, transiter_host, expected_result):
    actual_result = None
    for __ in range(40):
        updates = requests.get(
            transiter_host + "/systems/" + system_id + "/feeds/GtfsRealtimeFeed/updates"
        ).json()
        if len(updates["updates"]) > 0:
            latest_update = updates["updates"][0]
            actual_result = latest_update.get("result")
            if (
                expected_result == actual_result
            ):
                return
        time.sleep(0.1)
        print(expected_result, actual_result)
        print(updates)
    assert actual_result == expected_result
