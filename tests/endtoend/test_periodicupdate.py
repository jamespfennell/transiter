import time

import requests

from . import gtfsrealtimegenerator


def test_periodic_update(system_id, install_system_1, transiter_host, source_server):

    __, realtime_feed_url = install_system_1(system_id, "0.5s")

    # Check that the realtime feed is initially failing
    _wait_for_update(system_id, transiter_host, "FAILURE", "EMPTY_FEED")

    # Then, check for a successful update (with the right hash?)
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(0, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    _wait_for_update(system_id, transiter_host, "SUCCESS", "UPDATED")

    # Then, check for a redundant update
    _wait_for_update(system_id, transiter_host, "SUCCESS", "NOT_NEEDED")

    # Empty feed
    source_server.put(realtime_feed_url, "")
    _wait_for_update(system_id, transiter_host, "FAILURE", "EMPTY_FEED")

    # Invalid feed content
    source_server.put(realtime_feed_url, "not a valid GTFS realtime message")
    _wait_for_update(system_id, transiter_host, "FAILURE", "PARSE_ERROR")

    # Finally, a new update
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(100, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    _wait_for_update(system_id, transiter_host, "SUCCESS", "UPDATED")

    # Download error (here a simulated 404)
    #
    # We put this last because deleting the resource from the source server kind of messes it up
    source_server.delete(realtime_feed_url)
    _wait_for_update(system_id, transiter_host, "FAILURE", "DOWNLOAD_ERROR")


def _wait_for_update(system_id, transiter_host, expected_status, expected_result):

    for __ in range(40):
        updates = requests.get(
            transiter_host + "/systems/" + system_id + "/feeds/GtfsRealtimeFeed/updates"
        ).json()
        if len(updates["updates"]) > 0:
            latest_update = updates["updates"][0]
            if (
                expected_status == latest_update["status"]
                and expected_result == latest_update["result"]
            ):
                return
        time.sleep(0.1)
    assert False, "No feed update with status={} and result={}".format(
        expected_status, expected_result
    )
