import pytest
from . import gtfs_realtime_pb2 as gtfs
from haversine import haversine
from . import shared
from . import client


ROUTE_ID = "A"
STOP_1_ID = "stop_1_id"
STOP_2_ID = "stop_2_id"
STOP_3_ID = "stop_3_id"
VEHICLE_1 = client.Vehicle(
    id="vehicle_1_id",
    trip=client.TripReference(
        id="trip_1_id",
        vehicle=None,
    ),
    latitude=40.75,
    longitude=-73.875,
)
VEHICLE_2 = client.Vehicle(
    id="vehicle_2_id",
    trip=client.TripReference(
        id="trip_2_id",
        vehicle=None,
    ),
    latitude=30,
    longitude=-150,
)
VEHICLE_3 = client.Vehicle(
    id="vehicle_3_id",
    trip=client.TripReference(
        id="trip_3_id",
        vehicle=None,
    ),
    latitude=50,
    longitude=-50,
)
GTFS_STATIC_TXTAR = f"""
-- routes.txt --
route_id,route_type
{ROUTE_ID},2
-- stops.txt --
stop_id
{STOP_1_ID}
{STOP_2_ID}
{STOP_3_ID}
"""


def test_list_vehicles(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_vehicles_test
    got_list_vehicles = transiter_client.list_vehicles(system_id)
    assert got_list_vehicles.vehicles == [VEHICLE_1, VEHICLE_2, VEHICLE_3]


def test_list_vehicles_with_pagination(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_vehicles_test

    got_list_vehicles = transiter_client.list_vehicles(system_id, params={"limit": 2})
    assert got_list_vehicles == client.ListVehiclesResponse(
        vehicles=[VEHICLE_1, VEHICLE_2],
        nextId=VEHICLE_3.id,
    )

    got_list_vehicles = transiter_client.list_vehicles(
        system_id, params={"limit": 2, "first_id": got_list_vehicles.nextId}
    )
    assert got_list_vehicles == client.ListVehiclesResponse(
        vehicles=[VEHICLE_3], nextId=None
    )


def test_list_vehicles_with_filtering(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_vehicles_test

    got_list_vehicles = transiter_client.list_vehicles(
        system_id,
        params={
            "only_return_specified_ids": True,
            "id[]": [VEHICLE_2.id, VEHICLE_3.id],
        },
    )
    assert got_list_vehicles.vehicles == [VEHICLE_2, VEHICLE_3]


def test_get_vehicle(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_vehicles_test

    for want_vehicle in [VEHICLE_1, VEHICLE_2, VEHICLE_3]:
        got_vehicle = transiter_client.get_vehicle(system_id, want_vehicle.id)
        assert got_vehicle == want_vehicle


SEARCH_LATITUDE = 40.755
SEARCH_LONGITUDE = -73.8755


@pytest.mark.parametrize(
    "search_distance,want_vehicles",
    [
        # No vehicles within 0.5km of relative location
        (0, []),
        # Only vehicle 1 is within 1km of the relative location
        (1, [VEHICLE_1]),
        # All vehicles returned in order of distance
        (40075, [VEHICLE_1, VEHICLE_3, VEHICLE_2]),
    ],
)
def test_geographic_search(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
    search_distance,
    want_vehicles,
):
    _ = system_for_vehicles_test

    dist_km = haversine(
        (SEARCH_LATITUDE, SEARCH_LONGITUDE), (VEHICLE_1.latitude, VEHICLE_1.longitude)
    )
    assert dist_km > 0.5 and dist_km < 1.0

    got_list_vehicles = transiter_client.list_vehicles(
        system_id,
        params={
            "search_mode": "DISTANCE",
            "latitude": SEARCH_LATITUDE,
            "longitude": SEARCH_LONGITUDE,
            "max_distance": search_distance,
        },
    )
    assert got_list_vehicles.vehicles == want_vehicles


def test_trip_view(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_vehicles_test

    trip = transiter_client.get_trip(system_id, ROUTE_ID, VEHICLE_1.trip.id)
    assert trip.vehicle == client.VehicleReference(
        id=VEHICLE_1.id,
    )


def test_stop_view(
    system_for_vehicles_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_vehicles_test

    stop = transiter_client.get_stop(system_id, STOP_1_ID)
    assert len(stop.stopTimes) == 1

    assert stop.stopTimes[0].trip.vehicle == client.VehicleReference(
        id=VEHICLE_1.id,
    )


@pytest.fixture
def system_for_vehicles_test(
    system_id,
    install_system_using_txtar,
    transiter_client: client.TransiterClient,
    source_server: shared.SourceServerClient,
):
    __, realtime_feed_url = install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)
    source_server.put(
        realtime_feed_url,
        build_gtfs_rt_message().SerializeToString(),
    )
    transiter_client.perform_feed_update(system_id, shared.GTFS_REALTIME_FEED_ID)


def build_gtfs_rt_message():
    def vehicle_entity(vehicle: client.Vehicle):
        return gtfs.FeedEntity(
            id=f"vehicle_{vehicle.id}",
            vehicle=gtfs.VehiclePosition(
                vehicle=gtfs.VehicleDescriptor(id=vehicle.id),
                trip=gtfs.TripDescriptor(trip_id=vehicle.trip.id),
                position=gtfs.Position(
                    latitude=vehicle.latitude,
                    longitude=vehicle.longitude,
                ),
            ),
        )

    def trip_entity(vehicle: client.Vehicle, stop_time_updates):
        return gtfs.FeedEntity(
            id=f"trip_{vehicle.trip.id}",
            trip_update=gtfs.TripUpdate(
                vehicle=gtfs.VehicleDescriptor(id=vehicle.id),
                trip=gtfs.TripDescriptor(
                    trip_id=vehicle.trip.id, route_id=ROUTE_ID, direction_id=True
                ),
                stop_time_update=stop_time_updates,
            ),
        )

    def stop_time_update(stop_id, arrival_time, stop_sequence):
        return gtfs.TripUpdate.StopTimeUpdate(
            arrival=gtfs.TripUpdate.StopTimeEvent(time=arrival_time),
            departure=gtfs.TripUpdate.StopTimeEvent(time=arrival_time + 15),
            stop_id=stop_id,
            stop_sequence=stop_sequence + 25,
        )

    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=0),
        entity=[
            vehicle_entity(VEHICLE_1),
            vehicle_entity(VEHICLE_2),
            vehicle_entity(VEHICLE_3),
            trip_entity(
                VEHICLE_1,
                [
                    stop_time_update(STOP_1_ID, 300, 1),
                    stop_time_update(STOP_2_ID, 800, 2),
                    stop_time_update(STOP_3_ID, 850, 3),
                ],
            ),
            trip_entity(VEHICLE_2, []),
            trip_entity(VEHICLE_3, []),
        ],
    )
