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
ROUTE_IDS = {"A", "B", "RouteId"}
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

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "Test System"


@pytest.mark.parametrize("sync", [True, False])
def _test_install_system__stops(system_id, install_system_1, transiter_host, sync):

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
def _test_install_system__transfers(system_id, install_system_1, transiter_host, sync):

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
    actual_route_ids = set([route["id"] for route in routes_response["routes"]])
    assert ROUTE_IDS == actual_route_ids

    route_response =   requests.get(
        transiter_host + "/systems/" + system_id + "/routes/RouteId"
    ).json()
    assert "RouteId" == route_response["id"]
    assert "RouteColor" == route_response["color"]
    assert "RouteTextColor" == route_response["textColor"]
    assert "RouteShortName" == route_response["shortName"]
    assert "RouteLongName" == route_response["longName"]
    assert "RouteDesc" == route_response["description"]
    assert 50 == route_response["sortOrder"]
    assert "PHONE_AGENCY" == route_response["continuousPickup"]
    assert "COORDINATE_WITH_DRIVER" == route_response["continuousDropOff"]
    assert "SUBWAY" == route_response["type"]


@pytest.mark.parametrize("sync", [True, False])
def test_install_system__feeds(system_id, install_system_1, transiter_host, sync):

    install_system_1(system_id, sync=sync)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    feeds_count = system_response["feeds"]["count"]
    assert len(FEED_IDS) == int(feeds_count)

    feeds_response = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds"
    ).json()
    actual_feed_ids = set([feed["id"] for feed in feeds_response["feeds"]])
    assert FEED_IDS == actual_feed_ids


@pytest.mark.parametrize("sync", [True, False])
def _test_install_system__success__service_map_stop(
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
def _test_install_system__service_map_route(
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


def test_install_system__agency(system_id, install_system_1, transiter_host):
    install_system_1(system_id)

    agencies_response = requests.get(
        transiter_host + "/systems/" + system_id + "/agencies"
    ).json()["agencies"]
    assert 1 == len(agencies_response)

    agency_response = requests.get(
        transiter_host + "/systems/" + system_id + "/agencies/AgencyId"
    ).json()
    assert "AgencyId" == agency_response["id"]
    assert "AgencyName" == agency_response["name"]
    assert "AgencyUrl" == agency_response["url"]
    assert "AgencyTimezone" == agency_response["timezone"]
    assert "AgencyLanguage" == agency_response["language"]
    assert "AgencyPhone" == agency_response["phone"]
    assert "AgencyFareUrl" == agency_response["fareUrl"]
    assert "AgencyEmail" == agency_response["email"]


@pytest.mark.parametrize("sync", [True, False])
def _test_install_system__bad_config(system_id, install_system, transiter_host, sync):
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
  - id: feed_1
    url: {feed_url}
    parser: GTFS_STATIC
    requiredForInstall: false

"""

  
@pytest.mark.parametrize("sync", [True, False])
def _test_install_system__bad_update(system_id, install_system, transiter_host, sync):
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


def _test_update_static_entities(
    system_id, install_system_1, transiter_host, source_server, updated_gtfs_zip
):
    static_feed_url, __ = install_system_1(system_id)

    source_server.put(static_feed_url, updated_gtfs_zip)

    response = requests.post(
        transiter_host + "/systems/" + system_id + "/feeds/gtfsstatic?sync=true"
    ).json()

    assert response["status"] != "FAILURE"


@pytest.mark.parametrize("sync", [True, False])
def test_delete(system_id, install_system_1, transiter_host, sync):
    install_system_1(system_id)

    response = requests.delete(
        transiter_host + "/admin/systems/" + system_id + "?sync=" + str(sync).lower()
    )
    response.raise_for_status()

    response = requests.get(transiter_host + "/systems/" + system_id)
    assert response.status_code == 404


def test_update_system(system_id, install_system, transiter_host):
    config = """
    name: {}

    feeds:
      - id: feed_1
        requiredForInstall: false
        autoUpdateEnabled: true
        autoUpdatePeriod: {}s
        url: transiter.io
        parser: GTFS_STATIC
    """

    install_system(system_id, config.format("name1", 5))

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "name1"
    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    assert "5s" == feed_data["autoUpdatePeriod"]

    install_system(system_id, config.format("name2", 15))

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "name2"
    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    assert "15s" == feed_data["autoUpdatePeriod"]
