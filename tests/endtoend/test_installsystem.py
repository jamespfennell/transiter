import pytest
import requests
from haversine import haversine

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
    "StopID",
    "ParentStopID",
}
ROUTE_IDS = {"A", "B", "RouteID"}
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


def test_install_system__stops(system_id, install_system_1, transiter_host):

    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    stops_count = system_response["stops"]["count"]
    assert len(STOP_IDS) == int(stops_count)

    stops_response = requests.get(
        transiter_host + "/systems/" + system_id + "/stops"
    ).json()
    actual_stop_ids = set([stop["id"] for stop in stops_response["stops"]])
    assert STOP_IDS == actual_stop_ids

    stop_response = requests.get(
        transiter_host + "/systems/" + system_id + "/stops/StopID"
    ).json()

    def assert_stop_response_for_StopID(stop_response):
        assert "StopID" == stop_response["id"]
        assert "StopCode" == stop_response["code"]
        assert "StopName" == stop_response["name"]
        assert "StopDesc" == stop_response["description"]
        assert "ZoneId" == stop_response["zoneId"]
        assert 40.7527 == stop_response["latitude"]
        assert -73.9772 == stop_response["longitude"]
        assert "StopUrl" == stop_response["url"]
        assert "STOP" == stop_response["type"]
        assert "StopTimezone" == stop_response["timezone"]
        assert True == stop_response["wheelchairBoarding"]
        assert "PlatformCode" == stop_response["platformCode"]
        assert "ParentStopID" == stop_response["parentStop"]["id"]

    assert_stop_response_for_StopID(stop_response)

    parent_stop_response = requests.get(
        transiter_host + "/systems/" + system_id + "/stops/ParentStopID"
    ).json()
    assert 1 == len(parent_stop_response["childStops"])
    assert "StopID" == parent_stop_response["childStops"][0]["id"]
    assert "STATION" == parent_stop_response["type"]

    # Geolocation
    relative_lat_lon = (40.7559, -73.9871)
    stop_lat_lon = (stop_response["latitude"], stop_response["longitude"])

    dist_km = haversine(relative_lat_lon, stop_lat_lon)
    assert dist_km > 0.9 and dist_km < 1.0

    query_params = {
        "search_mode": "DISTANCE",
        "latitude": relative_lat_lon[0],
        "longitude": relative_lat_lon[1],
        "max_distance": 1.0,
    }
    stops_response_geo = requests.get(
        transiter_host + "/systems/" + system_id + "/stops", params=query_params
    ).json()
    print(stops_response_geo)
    stops_geo = stops_response_geo["stops"]

    # Only 'StopID' is within 1km of the relative location
    assert 1 == len(stops_geo)
    assert_stop_response_for_StopID(stops_geo[0])

    query_params_closer = {**query_params, "max_distance": 0.5}
    stops_response_geo_empty = requests.get(
        transiter_host + "/systems/" + system_id + "/stops", params=query_params_closer
    ).json()

    # No stops within 0.5km of relative location
    assert 0 == len(stops_response_geo_empty["stops"])

    query_params_all_of_earth = {**query_params, "max_distance": 40075}
    stops_response_geo_all = requests.get(
        transiter_host + "/systems/" + system_id + "/stops",
        params=query_params_all_of_earth,
    ).json()

    # All stops returned
    assert STOP_IDS == set(stop["id"] for stop in stops_response_geo_all["stops"])


def test_install_system__transfers(system_id, install_system_1, transiter_host):
    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    stops_count = system_response["transfers"]["count"]
    assert 3 == int(stops_count)

    stops_response = requests.get(
        transiter_host + "/systems/" + system_id + "/transfers"
    ).json()["transfers"]
    actual_transfer_tuples = set(
        (transfer["fromStop"]["id"], transfer["toStop"]["id"])
        for transfer in stops_response
    )
    assert {("2COL", "1C"), ("2MEX", "1E"), ("1E", "2MEX")} == actual_transfer_tuples

    stop_response = requests.get(
        transiter_host + "/systems/" + system_id + "/stops/2COL"
    ).json()
    assert 1 == len(stop_response["transfers"])
    assert "TIMED" == stop_response["transfers"][0]["type"]
    assert 300 == stop_response["transfers"][0]["minTransferTime"]
    assert "1C" == stop_response["transfers"][0]["toStop"]["id"]

    stop_response = requests.get(
        transiter_host + "/systems/" + system_id + "/stops/1C"
    ).json()
    assert 0 == len(stop_response["transfers"])


def test_install_system__routes(system_id, install_system_1, transiter_host):

    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    routes_count = system_response["routes"]["count"]
    assert len(ROUTE_IDS) == int(routes_count)

    routes_response = requests.get(
        transiter_host + "/systems/" + system_id + "/routes"
    ).json()
    actual_route_ids = set([route["id"] for route in routes_response["routes"]])
    assert ROUTE_IDS == actual_route_ids

    route_response = requests.get(
        transiter_host + "/systems/" + system_id + "/routes/RouteID"
    ).json()
    assert "RouteID" == route_response["id"]
    assert "RouteColor" == route_response["color"]
    assert "RouteTextColor" == route_response["textColor"]
    assert "RouteShortName" == route_response["shortName"]
    assert "RouteLongName" == route_response["longName"]
    assert "RouteDesc" == route_response["description"]
    assert 50 == route_response["sortOrder"]
    assert "PHONE_AGENCY" == route_response["continuousPickup"]
    assert "COORDINATE_WITH_DRIVER" == route_response["continuousDropOff"]
    assert "SUBWAY" == route_response["type"]


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


def test_install_system__service_map_route(
    system_id, install_system_1, transiter_host
):
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

    response = requests.delete(
        transiter_host + "/systems/" + system_id
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
        schedulingPolicy: PERIODIC
        updatePeriodS: {}
        url: transiter.io
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
