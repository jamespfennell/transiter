import time

import requests

from . import gtfsrealtimegenerator


def test_auto_update(install_system_1, transiter_host, source_server):

    __, realtime_feed_url = install_system_1("test_auto_update", "1 second")

    # Check that the realtime feed is initially failing
    _wait_for_update(transiter_host, "FAILURE", "EMPTY_FEED")

    # Then, check for a successful update (with the right hash?)
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(0, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    _wait_for_update(transiter_host, "SUCCESS", "UPDATED")

    # Then, check for a redundant update
    _wait_for_update(transiter_host, "SUCCESS", "NOT_NEEDED")

    # Finally, a new update
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(100, [])
    source_server.put(realtime_feed_url, feed_1.build_feed())
    _wait_for_update(transiter_host, "SUCCESS", "UPDATED")


def _wait_for_update(transiter_host, expected_status, expected_sub_status):

    for __ in range(40):
        updates = requests.get(
            transiter_host + "/systems/test_auto_update/feeds/GtfsRealtimeFeed/updates"
        ).json()
        if len(updates) > 0:
            latest_update = updates[0]
            if (
                expected_status == latest_update["status"]
                and expected_sub_status == latest_update["explanation"]
            ):
                return
        time.sleep(0.1)
    assert False, "No feed update with status={} and explanation={}".format(
        expected_status, expected_sub_status
    )
