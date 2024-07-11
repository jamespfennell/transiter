from haversine import haversine
from . import shared
from . import client
from . import gtfs_utils
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
    stopTimes=[],
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
    stopTimes=[],
)


def test_stop(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, GTFS_STATIC_TXTAR)

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
    install_system,
    transiter_client: client.TransiterClient,
    search_distance,
    want_stops,
):
    install_system(system_id, GTFS_STATIC_TXTAR)

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
    install_system,
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

    install_system(system_id, gtfs_static_txtar)

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

def test_trip_headsigns(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
    source_server: shared.SourceServerClient,):

    stop_1 = "stop_1_id"
    stop_2 = "stop_2_id"
    route_1_id = "route_id_1"
    route_2_id = "route_id_2"
    trip_1_id = "trip_1_id"
    trip_2_id = "trip_2_id"
    gtfs_static_txtar = f"""
    -- stops.txt --
    stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station,stop_code,stop_desc,zone_id,stop_url,stop_timezone,wheelchair_boarding,level_id,platform_code
    {stop_1},,30,50,1,,,,,,,,,
    {stop_2},,80,90,1,,,,,,,,,
    -- agency.txt --
    agency_id,agency_name,agency_url,agency_timezone
    AgencyID,AgencyName,AgencyURL,AgencyTimezone
    -- calendar.txt --
    service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
    Weekday,1,1,1,1,1,0,0,20180101,20181231
    -- routes.txt --
    route_id,route_type
    {route_1_id},2
    {route_2_id},2
    -- trips.txt --
    route_id,service_id,trip_id,direction_id,trip_headsign
    {route_1_id},Weekday,{trip_1_id},1,headsign_1
    {route_2_id},Weekday,{trip_2_id},1,headsign_2
    -- stop_times.txt --
    trip_id,arrival_time,departure_time,stop_id,direction_id,stop_sequence,stop_headsign
    {trip_1_id},11:00:00,11:00:10,{stop_1},1,0,
    {trip_1_id},11:02:00,11:02:10,{stop_2},1,1,
    {trip_2_id},11:00:00,11:00:10,{stop_1},1,0,headsign_3
    {trip_2_id},11:02:00,11:02:10,{stop_2},1,1,headsign_4
    """

    __, realtime_feed_url = install_system(system_id, gtfs_static_txtar)

    trip_1_timetable = {
        stop_1: 300,
        stop_2: 600,
    }

    trip_2_timetable = {
        stop_1: 700,
        stop_2: 800,
    }

    # Add trip 1 times
    update_msg = gtfs_utils.build_gtfs_rt_trip_update_message(
            trip_1_id,
            route_1_id,
            0,
            trip_1_timetable,
            True,
        )
    # Append trip 2 times
    trip_2_entity = gtfs_utils.build_gtfs_rt_trip_update_message(
            trip_2_id,
            route_2_id,
            0,
            trip_2_timetable,
            True,
            feed_id="2",
        ).entity
    update_msg.entity.extend(trip_2_entity)

    # Perform the feed update
    source_server.put(realtime_feed_url, update_msg.SerializeToString())
    transiter_client.perform_feed_update(
        system_id, shared.GTFS_REALTIME_FEED_ID
    )

    # Validate headsigns at STOP_1
    stop_1 = transiter_client.get_stop(system_id, stop_1)
    stop_1_stop_times = stop_1.stopTimes
    trip_1_stop_times = [
        stop_time
        for stop_time in stop_1_stop_times
        if stop_time.trip.id == trip_1_id
    ]
    trip_2_stop_times = [
        stop_time
        for stop_time in stop_1_stop_times
        if stop_time.trip.id == trip_2_id
    ]

    assert len(trip_1_stop_times) == 1
    assert trip_1_stop_times[0].headsign == "headsign_1"

    # Trip 2 has a headsign "headsign_2" defined in trips.txt,
    # but the stop_times.txt file overrides it with "headsign_3
    assert len(trip_2_stop_times) == 1
    assert trip_2_stop_times[0].headsign == "headsign_3"

    # Validate headsigns at STOP_2
    stop_2 = transiter_client.get_stop(system_id, stop_2)
    stop_2_stop_times = stop_2.stopTimes
    trip_1_stop_times = [
        stop_time
        for stop_time in stop_2_stop_times
        if stop_time.trip.id == trip_1_id
    ]
    trip_2_stop_times = [
        stop_time
        for stop_time in stop_2_stop_times
        if stop_time.trip.id == trip_2_id
    ]

    assert len(trip_1_stop_times) == 1
    assert trip_1_stop_times[0].headsign == "headsign_1"

    # Trip 2 has a headsign "headsign_2" defined in trips.txt,
    # but the stop_times.txt file overrides it with "headsign_4
    assert len(trip_2_stop_times) == 1
    assert trip_2_stop_times[0].headsign == "headsign_4"
