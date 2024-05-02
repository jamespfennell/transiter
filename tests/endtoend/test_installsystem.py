import requests
from . import client

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


def test_install_system__basic_data(system_id, install_system_1, transiter_host):

    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "Test System"


def test_install_system__feeds(system_id, install_system_1, transiter_host):

    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    feeds_count = system_response["feeds"]["count"]
    assert len(FEED_IDS) == int(feeds_count)

    feeds_response = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds"
    ).json()
    actual_feed_ids = set([feed["id"] for feed in feeds_response["feeds"]])
    assert FEED_IDS == actual_feed_ids


def test_install_system__success__service_map_stop(
    system_id, install_system_1, transiter_host
):
    install_system_1(system_id)

    for stop_id, usual_route in STOP_ID_TO_USUAL_ROUTES.items():
        stop_response = requests.get(
            "{}/systems/{}/stops/{}".format(transiter_host, system_id, stop_id)
        ).json()
        actual = None
        for service_map in stop_response["serviceMaps"]:
            if service_map["configId"] != "weekday":
                continue
            actual = [route["id"] for route in service_map["routes"]]
        assert usual_route == actual


def test_install_system__service_map_route(system_id, install_system_1, transiter_host):
    install_system_1(system_id)

    for route_id, usual_stops in ROUTE_ID_TO_USUAL_ROUTE.items():
        route_response = requests.get(
            "{}/systems/{}/routes/{}".format(transiter_host, system_id, route_id)
        ).json()
        actual_stops = None
        for service_map in route_response["serviceMaps"]:
            if service_map["configId"] != "alltimes":
                continue
            actual_stops = [stop["id"] for stop in service_map["stops"]]
        assert usual_stops == actual_stops


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


def _test_install_system__bad_config(system_id, install_system, transiter_host):
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


def _test_install_system__bad_update(system_id, install_system, transiter_host):
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
        transiter_host + "/systems/" + system_id + "/feeds/gtfsstatic"
    ).json()

    assert response["status"] != "FAILURE"


def test_delete(system_id, install_system_1, transiter_host):
    install_system_1(system_id)

    response = requests.delete(transiter_host + "/systems/" + system_id)
    response.raise_for_status()

    response = requests.get(transiter_host + "/systems/" + system_id)
    assert response.status_code == 404


def test_update_system(system_id, install_system, transiter_host):
    config = """
    name: {}

    feeds:
      - id: feed_1
        requiredForInstall: false
        schedulingPolicy: PERIODIC
        updatePeriodS: {}
        url: transiter.dev
        parser: GTFS_STATIC
    """

    install_system(system_id, config.format("name1", 5))

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "name1"
    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    # TODO: renable
    # assert "5" == feed_data["updatePeriodS"]

    install_system(system_id, config.format("name2", 15))

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "name2"
    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    # TODO: renable
    # assert "15" == feed_data["updatePeriodS"]
