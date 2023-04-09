import requests


def test_gtfs_static_feed_flush(system_id, install_system_1, transiter_host):
    install_system_1(system_id)

    requests.post(
        transiter_host + "/systems/" + system_id + "/feeds/gtfsstatic/flush"
    )
    system_response = requests.get(transiter_host + "/systems/" + system_id).json()

    # (1) Verify all of the stops were removed
    assert 0 == system_response["stops"]["count"]

    # (2) Verify all of the routes were removed
    assert 0 == system_response["routes"]["count"]
