from haversine import haversine
from . import client

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

CHILD_STOP_REFERENCE = client.StopReference(id="StopID")

CHILD_STOP = client.Stop(
    id="StopID",
    code="StopCode",
    name="StopName",
    description="StopDesc",
    zoneId="ZoneId",
    latitude=40.7527,
    longitude=-73.9772,
    url="StopUrl",
    type="PLATFORM",
    timezone="StopTimezone",
    wheelchairBoarding=True,
    platformCode="PlatformCode",
    parentStop=client.StopReference(id="ParentStopID"),
    childStops=[],
)


def test_stop(
    system_id,
    install_system_1,
    transiter_client: client.TransiterClient,
):
    install_system_1(system_id)

    system = transiter_client.get_system(system_id)
    assert int(system.stops.count) == len(STOP_IDS)

    got_all_stops = transiter_client.list_stops(system_id)
    got_all_stop_ids = set([stop.id for stop in got_all_stops.stops])
    assert STOP_IDS == got_all_stop_ids

    got_child_stop = transiter_client.get_stop(system_id, "StopID")
    assert got_child_stop == CHILD_STOP

    got_parent_stop = transiter_client.get_stop(system_id, "ParentStopID")
    assert got_parent_stop.childStops == [CHILD_STOP_REFERENCE]

    # Geolocation
    # First we verify that the child stop is between 0.9 and 1km of the search point.
    relative_lat_lon = (40.7559, -73.9871)
    stop_lat_lon = (got_child_stop.latitude, got_child_stop.longitude)
    dist_km = haversine(relative_lat_lon, stop_lat_lon)
    assert dist_km > 0.9 and dist_km < 1.0

    query_params = {
        "search_mode": "DISTANCE",
        "latitude": relative_lat_lon[0],
        "longitude": relative_lat_lon[1],
        "max_distance": 1.0,
    }
    got_geo_stops = transiter_client.list_stops(system_id, query_params)
    # Only 'StopID' is within 1km of the relative location
    assert got_geo_stops.stops == [CHILD_STOP]

    query_params_closer = {**query_params, "max_distance": 0.5}
    got_geo_stops = transiter_client.list_stops(system_id, query_params_closer)
    # No stops within 0.5km of relative location
    assert got_geo_stops.stops == []

    query_params_all_of_earth = {**query_params, "max_distance": 40075}
    got_geo_stops = transiter_client.list_stops(system_id, query_params_all_of_earth)
    # All stops returned
    assert STOP_IDS == set(stop.id for stop in got_geo_stops.stops)
