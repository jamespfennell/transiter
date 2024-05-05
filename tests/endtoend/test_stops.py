from haversine import haversine
from . import client
import pytest


GTFS_STATIC_TXTAR = """
-- stops.txt --
stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station,stop_code,stop_desc,zone_id,stop_url,stop_timezone,wheelchair_boarding,level_id,platform_code
StopID,StopName,40.7527,-73.9772,0,ParentStopID,StopCode,StopDesc,ZoneId,StopUrl,StopTimezone,1,LevelId,PlatformCode
ParentStopID,,30,50,1,,,,,,,,,
"""
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
    transfers=[],
    serviceMaps=[],
    alerts=[],
)
PARENT_STOP = client.Stop(
    id="ParentStopID",
    code=None,
    name=None,
    description=None,
    zoneId=None,
    latitude=30,
    longitude=50,
    url=None,
    type="STATION",
    timezone=None,
    wheelchairBoarding=None,
    platformCode=None,
    parentStop=None,
    childStops=[
        client.StopReference(id="StopID"),
    ],
    transfers=[],
    serviceMaps=[],
    alerts=[],
)
PARENT_STOP = client.Stop(
    id="ParentStopID",
    code=None,
    name=None,
    description=None,
    zoneId=None,
    latitude=30,
    longitude=50,
    url=None,
    type="STATION",
    timezone=None,
    wheelchairBoarding=None,
    platformCode=None,
    parentStop=None,
    childStops=[
        client.StopReference(id="StopID"),
    ],
    transfers=[],
    serviceMaps=[],
)


def test_stop(
    system_id,
    install_system_using_txtar,
    transiter_client: client.TransiterClient,
):
    install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)

    got_system = transiter_client.get_system(system_id)
    assert got_system.stops == client.ChildResources(
        count=2, path=f"systems/{system_id}/stops"
    )

    # We skip service maps because those are tested in their own test.
    params = {"skip_service_maps": "true"}

    got_all_stops = transiter_client.list_stops(system_id, params)
    assert got_all_stops.stops == [PARENT_STOP, CHILD_STOP]

    for want_stop in [PARENT_STOP, CHILD_STOP]:
        got_stop = transiter_client.get_stop(system_id, want_stop.id, params)
        assert got_stop == want_stop


SEARCH_LATITUDE = 40.7559
SEARCH_LONGITUDE = -73.9871


@pytest.mark.parametrize(
    "search_distance,want_stops",
    [
        # No stops within 0.5km of relative location
        (0, []),
        # Only 'StopID' is within 1km of the relative location
        (1, [CHILD_STOP]),
        # All stops returned in order of distance
        (40075, [CHILD_STOP, PARENT_STOP]),
    ],
)
def test_geographic_search(
    system_id,
    install_system_using_txtar,
    transiter_client: client.TransiterClient,
    search_distance,
    want_stops,
):
    install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)

    # First we verify that the child stop is between 0.9 and 1km of the search point.
    stop_lat_lon = (CHILD_STOP.latitude, CHILD_STOP.longitude)
    dist_km = haversine((SEARCH_LATITUDE, SEARCH_LONGITUDE), stop_lat_lon)
    assert dist_km > 0.9 and dist_km < 1.0

    query_params = {
        "search_mode": "DISTANCE",
        "latitude": SEARCH_LATITUDE,
        "longitude": SEARCH_LONGITUDE,
        "max_distance": search_distance,
        # We skip service maps because those are tested in their own test.
        "skip_service_maps": "true",
    }
    got_geo_stops = transiter_client.list_stops(system_id, query_params)
    assert got_geo_stops.stops == want_stops


def test_list_stops_pagination(
    system_id,
    install_system_using_txtar,
    transiter_client: client.TransiterClient,
):
    def stop_id(i):
        return f"stop_{i:03d}"

    gtfs_static_txtar = """
    -- stops.txt --
    stop_id
    """
    for i in range(150):
        gtfs_static_txtar += stop_id(i) + "\n"

    install_system_using_txtar(system_id, gtfs_static_txtar)

    got_all_stops = transiter_client.list_stops(system_id)
    got_stop_ids = [stop.id for stop in got_all_stops.stops]
    assert got_stop_ids == [stop_id(i) for i in range(100)]
    assert got_all_stops.nextId == stop_id(100)

    got_all_stops = transiter_client.list_stops(
        system_id,
        params={
            "first_id": got_all_stops.nextId,
        },
    )
    got_stop_ids = [stop.id for stop in got_all_stops.stops]
    assert got_stop_ids == [stop_id(i) for i in range(100, 150)]
    assert got_all_stops.nextId == None
