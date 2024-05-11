from . import gtfs_realtime_pb2 as gtfs
from . import client
from . import shared
import dataclasses
import typing


STOP_1 = "stop-1"
STOP_2 = "stop-2"
STOP_3 = "stop-3"
STOP_4 = "stop-4"
STOP_5 = "stop-5"
STOP_6 = "stop-6"
STOP_7 = "stop-7"
ROUTE_ID = "A"

GTFS_STATIC_TXTAR = f"""
-- stops.txt --
stop_id
{STOP_1}
{STOP_2}
{STOP_3}
{STOP_4}
{STOP_5}
{STOP_6}
{STOP_7}
-- routes.txt --
route_id,route_type
{ROUTE_ID},2
B,2
-- calendar.txt --
service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
Weekday,1,1,1,1,1,0,0,20180101,20181231
Weekend,0,0,0,0,0,1,1,20180101,20181231
-- trips.txt --
route_id,service_id,trip_id,direction_id
{ROUTE_ID},Weekday,A-S-A01-Weekday-1100,1
{ROUTE_ID},Weekday,A-N-A01-Weekend-1100,0
{ROUTE_ID},Weekday,A-S-A01-Weekday-1130,1
{ROUTE_ID},Weekday,A-N-A01-Weekend-1130,0
-- stop_times.txt --
trip_id,arrival_time,departure_time,stop_id,stop_sequence
A-S-A01-Weekday-1100,11:00:00,11:00:10,{STOP_1},1
A-S-A01-Weekday-1100,11:02:00,11:02:10,{STOP_4},2
A-S-A01-Weekday-1100,11:03:00,11:03:10,{STOP_5},3
A-S-A01-Weekday-1130,11:30:00,11:30:10,{STOP_1},1
A-S-A01-Weekday-1130,11:32:00,11:32:10,{STOP_4},2
A-S-A01-Weekday-1130,11:33:00,11:33:10,{STOP_5},3
A-S-A01-Weekday-1130,11:34:00,11:34:10,{STOP_7},4
"""


STOP_ID_TO_USUAL_ROUTES = {
    STOP_1: [ROUTE_ID],
    STOP_2: [],
    STOP_3: [],
    STOP_4: [ROUTE_ID],
    STOP_5: [ROUTE_ID],
    STOP_6: [],
    STOP_7: [ROUTE_ID],
}
ROUTE_ID_TO_USUAL_STOPS = {"A": [STOP_1, STOP_4, STOP_5, STOP_7], "B": []}


def test_static_stop_view(
    system_id, install_system, transiter_client: client.TransiterClient
):
    install_system(system_id, GTFS_STATIC_TXTAR)

    for stop_id, want_route_ids in STOP_ID_TO_USUAL_ROUTES.items():
        print("checking", stop_id)
        stop = transiter_client.get_stop(system_id, stop_id)
        got_routes = None
        for service_map in stop.serviceMaps:
            if service_map.configId != "weekday":
                continue
            got_routes = service_map.routes
        assert got_routes == [
            client.RouteReference(id=route_id) for route_id in want_route_ids
        ]


def test_static_route_view(
    system_id, install_system, transiter_client: client.TransiterClient
):
    install_system(system_id, GTFS_STATIC_TXTAR)

    for route_id, want_stop_ids in ROUTE_ID_TO_USUAL_STOPS.items():
        route = transiter_client.get_route(system_id, route_id)
        got_stops = None
        for service_map in route.serviceMaps:
            if service_map.configId != "alltimes":
                continue
            got_stops = service_map.stops
        assert got_stops == [
            client.StopReference(id=stop_id) for stop_id in want_stop_ids
        ]


def test_realtime(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
    source_server: shared.SourceServerClient,
):
    __, realtime_feed_url = install_system(system_id, GTFS_STATIC_TXTAR)

    # (1) Regular case
    trip_1_stops = {
        STOP_1: 300,
        STOP_5: 1800,
        STOP_6: 2500,
    }
    trip_2_stops = {
        STOP_1: 300,
        STOP_2: 600,
        STOP_3: 800,
        STOP_4: 900,
        STOP_5: 1800,
    }
    feed_trips = [
        FeedTrip("trip_1", ROUTE_ID, trip_1_stops),
        FeedTrip("trip_2", ROUTE_ID, trip_2_stops),
    ]
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_trips,
        [STOP_1, STOP_2, STOP_3, STOP_4, STOP_5, STOP_6],
    )

    # (2) Old trips + new trips give an invalid map, but the update still happens
    # because old trips shouldn't count.
    trip_3_stops = {
        STOP_6: 250,
        STOP_5: 1800,
        STOP_1: 3000,
    }
    trip_4_stops = {
        STOP_5: 100,
        STOP_4: 900,
        STOP_3: 8000,
        STOP_2: 60000,
        STOP_1: 300000,
    }
    feed_trips = [
        FeedTrip("trip_3", ROUTE_ID, trip_3_stops),
        FeedTrip("trip_4", ROUTE_ID, trip_4_stops),
    ]
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_trips,
        list(reversed([STOP_1, STOP_2, STOP_3, STOP_4, STOP_5, STOP_6])),
    )

    # (3) With this update the map is now invalid so should not be updated, but the
    # trips are still updated successfully.
    trip_5_stops = {
        STOP_1: 250,
        STOP_5: 1800,
        STOP_6: 3000,
    }
    feed_trips = [
        FeedTrip("trip_3", ROUTE_ID, trip_3_stops),
        FeedTrip("trip_4", ROUTE_ID, trip_4_stops),
        FeedTrip("trip_5", ROUTE_ID, trip_5_stops),
    ]
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_trips,
        list(reversed([STOP_1, STOP_2, STOP_3, STOP_4, STOP_5, STOP_6])),
    )

    # (4) Valid map again
    trip_1_stops = {
        STOP_1: 300,
        STOP_5: 1800,
        STOP_6: 2500,
    }
    feed_trips = [
        FeedTrip("trip_1", ROUTE_ID, trip_1_stops),
    ]
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_trips,
        [STOP_1, STOP_5, STOP_6],
    )

    # (5) No more trips, service map is deleted.
    feed_trips = []
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_trips,
        [],
    )


@dataclasses.dataclass
class FeedTrip:
    trip_id: str
    route_id: str
    stops_dict: typing.Dict[str, int]


def _check_realtime_service_maps(
    system_id,
    transiter_client: client.TransiterClient,
    source_server: shared.SourceServerClient,
    realtime_feed_url,
    feed_trips: typing.List[FeedTrip],
    want_stop_ids,
):
    source_server.put(realtime_feed_url, build_gtfs_realtime_feed(feed_trips))
    transiter_client.perform_feed_update(system_id, shared.GTFS_REALTIME_FEED_ID)

    # (1) validate the service map appears in the route endpoints
    route = transiter_client.get_route(system_id, ROUTE_ID)
    want_stops = [client.StopReference(id=stop_id) for stop_id in want_stop_ids]
    got_stops = []
    for service_map in route.serviceMaps:
        if service_map.configId != "realtime":
            continue
        got_stops = service_map.stops
        break
    assert got_stops == want_stops

    # (2) validate the service map appears in the stop endpoints
    want_stop_ids = set(want_stop_ids)
    for stop in transiter_client.list_stops(system_id).stops:
        want_routes = []
        if stop.id in want_stop_ids:
            want_routes = [client.RouteReference(id=ROUTE_ID)]
        want_service_map = client.ServiceMapAtStop(
            configId="realtime",
            routes=want_routes,
        )

        got_routes = []
        for service_map in stop.serviceMaps:
            if service_map.configId != "realtime":
                continue
            got_routes = service_map.routes
            break
        got_service_map = client.ServiceMapAtStop(
            configId="realtime",
            routes=got_routes,
        )

        assert got_service_map == want_service_map


def build_gtfs_realtime_feed(feed_trips: typing.List[FeedTrip]):
    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(
            gtfs_realtime_version="2.0",
            timestamp=0,
        ),
        entity=[
            gtfs.FeedEntity(
                id=str(index),
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(
                        trip_id=trip.trip_id,
                        route_id=trip.route_id,
                        direction_id=True,
                    ),
                    stop_time_update=[
                        gtfs.TripUpdate.StopTimeUpdate(
                            stop_id=stop_id,
                            arrival=gtfs.TripUpdate.StopTimeEvent(time=time),
                            departure=gtfs.TripUpdate.StopTimeEvent(time=time + 15),
                        )
                        for stop_id, time in trip.stops_dict.items()
                    ],
                ),
            )
            for index, trip in enumerate(feed_trips)
        ],
    ).SerializeToString()
