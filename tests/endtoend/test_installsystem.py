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


def test_install_system(install_system_1, transiter_host):

    install_system_1("test_install_system")

    # (1) Verify all of the stops were installed
    system_response = requests.get(
        transiter_host + "/systems/test_install_system"
    ).json()
    stops_count = system_response["stops"]["count"]
    assert len(STOP_IDS) == stops_count

    stops_response = requests.get(
        transiter_host + "/systems/test_install_system/stops"
    ).json()
    actual_stop_ids = set([stop["id"] for stop in stops_response])
    assert STOP_IDS == actual_stop_ids

    # (2) Verify all of the routes were installed
    system_response = requests.get(
        transiter_host + "/systems/test_install_system"
    ).json()
    routes_count = system_response["routes"]["count"]
    assert len(ROUTE_IDS), routes_count

    routes_response = requests.get(
        transiter_host + "/systems/test_install_system/routes"
    ).json()
    actual_route_ids = set([route["id"] for route in routes_response])
    assert ROUTE_IDS == actual_route_ids

    # (3) Verify all of the feeds were installed
    system_response = requests.get(
        transiter_host + "/systems/test_install_system"
    ).json()
    feeds_count = system_response["feeds"]["count"]
    assert len(FEED_IDS) == feeds_count

    feeds_response = requests.get(
        transiter_host + "/systems/test_install_system/feeds"
    ).json()
    actual_feed_ids = set([feed["id"] for feed in feeds_response])
    assert FEED_IDS == actual_feed_ids

    # (4) Verify the service map is correct in the stops view
    for stop_id, usual_route in STOP_ID_TO_USUAL_ROUTES.items():
        stop_response = requests.get(
            "{}/systems/test_install_system/stops/{}".format(transiter_host, stop_id)
        ).json()
        if len(stop_response["service_maps"]) == 0:
            actual = []
        else:
            actual = [
                route["id"] for route in stop_response["service_maps"][0]["routes"]
            ]
        assert usual_route == actual

    # (5) Verify the service map is correct in the routes view
    for route_id, usual_stops in ROUTE_ID_TO_USUAL_ROUTE.items():
        route_response = requests.get(
            "{}/systems/test_install_system/routes/{}".format(transiter_host, route_id)
        ).json()
        for service_map in route_response["service_maps"]:
            if service_map["group_id"] != "any_time":
                continue
            actual_stops = [stop["id"] for stop in service_map["stops"]]
            assert usual_stops == actual_stops
            break
