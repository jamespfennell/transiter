import pytest
import requests

STOP_IDS = {
    "1A",
    "1B",
    "1C",
    "1D",
    "1E",
    "1F",
    "1G",
    "1AS",
    "1BS",
    "1CS",
    "1DS",
    "1ES",
    "1FS",
    "1GS",
    "1AN",
    "1BN",
    "1CN",
    "1DN",
    "1EN",
    "1FN",
    "1GN",
    "2COL",
    "2MEX",
}
ROUTE_IDS = {"A", "B"}
FEED_IDS = {"GtfsRealtimeFeed", "gtfsstatic"}
STOP_ID_TO_USUAL_ROUTES = {
    "1A": ["A"],
    "1B": [],
    "1C": [],
    "1D": ["A"],
    "1E": ["A"],
    "1F": [],
    "1G": ["A"],
}
ROUTE_ID_TO_USUAL_ROUTE = {"A": ["1A", "1D", "1E", "1G"], "B": []}


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__basic_data(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    # (0) Verify the system name was populated
    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "Test System"


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__stops(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    stops_count = system_response["stops"]["count"]
    assert len(STOP_IDS) == stops_count

    stops_response = requests.get(
        transiter_host + "/systems/" + system_id + "/stops"
    ).json()
    actual_stop_ids = set([stop["id"] for stop in stops_response])
    assert STOP_IDS == actual_stop_ids


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__transfers(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    stops_count = system_response["transfers"]["count"]
    assert 3 == stops_count

    stops_response = requests.get(
        transiter_host + "/systems/" + system_id + "/transfers"
    ).json()
    actual_transfer_tuples = set(
        (transfer["from_stop"]["id"], transfer["to_stop"]["id"])
        for transfer in stops_response
    )
    assert {("2COL", "1C"), ("2MEX", "1E"), ("1E", "2MEX")} == actual_transfer_tuples


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__routes(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    routes_count = system_response["routes"]["count"]
    assert len(ROUTE_IDS), routes_count

    routes_response = requests.get(
        transiter_host + "/systems/" + system_id + "/routes"
    ).json()
    actual_route_ids = set([route["id"] for route in routes_response])
    assert ROUTE_IDS == actual_route_ids


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__feeds(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    feeds_count = system_response["feeds"]["count"]
    assert len(FEED_IDS) == feeds_count

    feeds_response = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds"
    ).json()
    actual_feed_ids = set([feed["id"] for feed in feeds_response])
    assert FEED_IDS == actual_feed_ids


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__success__service_map_stop(
    system_id, install_system_1, transiter_host, sync
):

    install_system_1(system_id, sync=sync)

    for stop_id, usual_route in STOP_ID_TO_USUAL_ROUTES.items():
        stop_response = requests.get(
            "{}/systems/{}/stops/{}".format(transiter_host, system_id, stop_id)
        ).json()
        if len(stop_response["service_maps"]) == 0:
            actual = []
        else:
            actual = [
                route["id"] for route in stop_response["service_maps"][0]["routes"]
            ]
        assert usual_route == actual


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__service_map_route(
    system_id, install_system_1, transiter_host, sync
):

    install_system_1(system_id, sync=sync)

    for route_id, usual_stops in ROUTE_ID_TO_USUAL_ROUTE.items():
        route_response = requests.get(
            "{}/systems/{}/routes/{}".format(transiter_host, system_id, route_id)
        ).json()
        for service_map in route_response["service_maps"]:
            if service_map["group_id"] != "any_time":
                continue
            actual_stops = [stop["id"] for stop in service_map["stops"]]
            assert usual_stops == actual_stops
            break


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__agency(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    agencies_response = requests.get(
        transiter_host + "/systems/" + system_id + "/agencies"
    ).json()
    assert 1 == len(agencies_response)
    assert "Transiter Transit Agency" == agencies_response[0]["name"]


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__bad_config(install_system, transiter_host, sync):
    system_id = "test_install_system__fail_" + str(sync)

    install_system(
        system_id,
        "This is not a valid Transiter YAML config!",
        expected_status="INSTALL_FAILED",
    )

    for sub_entity in ["stops", "routes", "feeds"]:
        sub_entity_response = requests.get(
            transiter_host + "/systems/" + system_id + "/" + sub_entity
        )
        assert sub_entity_response.status_code == 404


SYSTEM_CONFIG = """
name: Test System

feeds:
  feed_1:
    http:
      url: {feed_url}
    parser:
      built_in: GTFS_STATIC
    required_for_install: true

"""


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__bad_update(install_system, transiter_host, sync):
    system_id = "test_install_system__update_" + str(sync)

    install_system(
        system_id,
        SYSTEM_CONFIG.format(feed_url="non_url"),
        expected_status="INSTALL_FAILED",
    )

    for sub_entity in ["stops", "routes", "feeds"]:
        sub_entity_response = requests.get(
            transiter_host + "/systems/" + system_id + "/" + sub_entity
        )
        assert sub_entity_response.status_code == 404


def test_update_static_entities(
    install_system_1, transiter_host, source_server, updated_gtfs_zip
):
    system_id = "test_update_static_entities"
    static_feed_url, __ = install_system_1(system_id)

    source_server.put(static_feed_url, updated_gtfs_zip)

    response = requests.post(
        transiter_host
        + "/systems/test_update_static_entities/feeds/gtfsstatic?sync=true"
    ).json()

    assert response["status"] != "FAILURE"


@pytest.mark.parametrize("sync", [True, False])
def test_delete(install_system_1, transiter_host, sync):
    system_id = "test_delete_" + str(sync)
    install_system_1(system_id)

    response = requests.delete(
        transiter_host + "/systems/" + system_id + "?sync=" + str(sync).lower()
    )
    if sync:
        assert response.status_code == 204
    else:
        assert response.status_code == 202

    response = requests.get(transiter_host + "/systems/" + system_id)
    assert response.status_code == 404


def test_update_system(install_system, transiter_host):
    system_id = "test_update_system"

    config = """
    name: test update system

    feeds:
      feed_1:
        parser:
          built_in: GTFS_STATIC
        http:
          url: transiter.io
        auto_update:
          period: {} seconds
    """

    install_system(system_id, config.format(5))

    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    assert 5 == feed_data["auto_update_period"]

    install_system(system_id, config.format(15))

    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    assert 15 == feed_data["auto_update_period"]
