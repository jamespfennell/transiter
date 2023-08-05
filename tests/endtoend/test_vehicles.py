import pytest
import requests
from . import gtfs_realtime_pb2 as gtfs
from haversine import haversine

VEHICLE_ID_1 = "vehicle_id_1"
VEHICLE_ID_2 = "vehicle_id_2"
VEHICLE_ID_3 = "vehicle_id_3"
VEHICLE_IDS = {VEHICLE_ID_1, VEHICLE_ID_2, VEHICLE_ID_3}
VEHICLE_1_LAT = 40.7527
VEHICLE_1_LON = -73.9772
TRIP_ID_1 = "trip_id_1"
TRIP_ID_2 = "trip_id_2"
TRIP_ID_3 = "trip_id_3"
ROUTE_ID = "A"
FIRST_STOP_ID = "1AS"


@pytest.mark.parametrize(
    "stop_id_to_time",
    [{
        FIRST_STOP_ID: 300,
        "1BS": 800,
        "1CS": 850,
    }],
)
@pytest.mark.parametrize(
    "vehicles",
    [
        {
            VEHICLE_ID_1: {
                "trip_id": TRIP_ID_1,
                "lat": VEHICLE_1_LAT,
                "lon": VEHICLE_1_LON,
            },
            VEHICLE_ID_2: {
                "trip_id": TRIP_ID_2,
                "lat": 50,
                "lon": -50,
            },
            VEHICLE_ID_3: {
                "trip_id": TRIP_ID_3,
                "lat": 150,
                "lon": -150,
            },
        },
    ],
)
class TestVehicles:

    def test_vehicle_view(self, install_system_1, system_id, transiter_host,
                          source_server, stop_id_to_time, vehicles):
        __, realtime_feed_url = install_system_1(
            system_id, only_process_full_entities="true")

        source_server.put(
            realtime_feed_url,
            build_gtfs_rt_message(stop_id_to_time,
                                  vehicles).SerializeToString(),
        )
        response = requests.post(
            f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed"
        ).json()
        print(response)

        # List vehicles
        response = requests.get(
            f"{transiter_host}/systems/{system_id}/vehicles").json()
        print(response)

        resp_vehicles = response["vehicles"]
        compare_vehicles_to_resp(vehicles, resp_vehicles)

        # List vehicles (pagination)
        paginated_vehicles = []
        next_id = None
        num_pages = 0
        while len(paginated_vehicles) < len(vehicles):
            query_params = {
                "limit": 2,
            }
            if next_id:
                query_params["first_id"] = next_id
            response = requests.get(
                f"{transiter_host}/systems/{system_id}/vehicles",
                params=query_params).json()
            assert len(response["vehicles"]) <= 2
            paginated_vehicles.extend(response["vehicles"])
            num_pages += 1

            if "nextId" not in response:
                break
            next_id = response["nextId"]

        compare_vehicles_to_resp(vehicles, paginated_vehicles)
        assert num_pages == 2

        # List vehicles by ids
        query_params = {
            "only_return_specified_ids": True,
            "id[]": [VEHICLE_ID_2, VEHICLE_ID_3],
        }
        response = requests.get(
            f"{transiter_host}/systems/{system_id}/vehicles",
            params=query_params).json()
        print(response)
        assert {VEHICLE_ID_2,
                VEHICLE_ID_3} == set(vehicle["id"]
                                     for vehicle in response["vehicles"])
        compare_vehicles_to_resp(vehicles, response["vehicles"], {
            VEHICLE_ID_2,
            VEHICLE_ID_3,
        })

        # Get vehicle
        for vehicle_id, vehicle in vehicles.items():
            resp_vehicle = requests.get(
                f"{transiter_host}/systems/{system_id}/vehicles/{vehicle_id}"
            ).json()
            compare_vehicle_to_resp({
                **vehicle, "id": vehicle_id
            }, resp_vehicle)

        # Geolocation
        relative_lat_lon = (40.7559, -73.9871)
        vehicle_1_lat_lon = (VEHICLE_1_LAT, VEHICLE_1_LON)

        dist_km = haversine(relative_lat_lon, vehicle_1_lat_lon)
        assert dist_km > 0.9 and dist_km < 1.0

        query_params = {
            "search_mode": "DISTANCE",
            "latitude": relative_lat_lon[0],
            "longitude": relative_lat_lon[1],
            "max_distance": 1.0,
        }

        response = requests.get(
            f"{transiter_host}/systems/{system_id}/vehicles",
            params=query_params).json()
        print(response)
        vehicles_geo = response["vehicles"]

        # Only 1st vehicle is within 1km of the relative location
        assert 1 == len(vehicles_geo)
        assert VEHICLE_ID_1 == vehicles_geo[0]["id"]

        query_params_closer = {**query_params, "max_distance": 0.5}
        response = requests.get(
            f"{transiter_host}/systems/{system_id}/vehicles",
            params=query_params_closer).json()

        # No vehicles within 0.5km of relative location
        assert 0 == len(response["vehicles"])

        query_params_all_of_earth = {**query_params, "max_distance": 40075}
        response = requests.get(
            f"{transiter_host}/systems/{system_id}/vehicles",
            params=query_params_all_of_earth).json()

        # All vehicles returned
        compare_vehicles_to_resp(vehicles, response["vehicles"])

    def test_trip_view(self, install_system_1, system_id, transiter_host,
                       source_server, stop_id_to_time, vehicles):
        __, realtime_feed_url = install_system_1(
            system_id, only_process_full_entities="true")

        source_server.put(
            realtime_feed_url,
            build_gtfs_rt_message(stop_id_to_time,
                                  vehicles).SerializeToString(),
        )
        response = requests.post(
            f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed"
        ).json()
        print(response)

        response = requests.get(
            f"{transiter_host}/systems/{system_id}/routes/{ROUTE_ID}/trips/{TRIP_ID_1}"
        ).json()
        print(response)

        assert response["id"] == TRIP_ID_1
        assert response["vehicle"]["id"] == VEHICLE_ID_1

    def test_stop_view(self, install_system_1, system_id, transiter_host,
                       source_server, stop_id_to_time, vehicles):
        __, realtime_feed_url = install_system_1(
            system_id, only_process_full_entities="true")

        source_server.put(
            realtime_feed_url,
            build_gtfs_rt_message(stop_id_to_time,
                                  vehicles).SerializeToString(),
        )
        response = requests.post(
            f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed"
        ).json()
        print(response)

        response = requests.get(
            f"{transiter_host}/systems/{system_id}/stops/{FIRST_STOP_ID}"
        ).json()
        print(response)

        stop_times = response["stopTimes"]
        assert len(stop_times) == 1

        stop_time = stop_times[0]
        assert stop_time["trip"]["id"] == TRIP_ID_1
        assert stop_time["trip"]["vehicle"]["id"] == VEHICLE_ID_1


def compare_vehicles_to_resp(vehicles, resp_vehicles, expected_ids=None):
    if expected_ids is None:
        expected_ids = set(vehicles.keys())
    assert len(expected_ids) == len(resp_vehicles)

    for vehicle_id in expected_ids:
        vehicle = vehicles[vehicle_id]
        resp_vehicles_with_id = [
            v for v in resp_vehicles if v["id"] == vehicle_id
        ]
        assert len(resp_vehicles_with_id) == 1

        resp_vehicle = resp_vehicles_with_id[0]
        compare_vehicle_to_resp({**vehicle, "id": vehicle_id}, resp_vehicle)


def compare_vehicle_to_resp(vehicle, resp_vehicle):
    assert resp_vehicle["id"] == vehicle["id"]
    assert resp_vehicle["latitude"] == vehicle["lat"]
    assert resp_vehicle["longitude"] == vehicle["lon"]
    assert resp_vehicle["trip"]["id"] == vehicle["trip_id"]
    assert resp_vehicle["trip"]["route"]["id"] == ROUTE_ID


def build_gtfs_rt_message(stop_id_to_time, vehicles):
    vehicles_entities = [
        gtfs.FeedEntity(
            id=f"vehicle_{idx}",
            vehicle=gtfs.VehiclePosition(
                vehicle=gtfs.VehicleDescriptor(id=vehicle_id),
                trip=gtfs.TripDescriptor(trip_id=vehicle["trip_id"]),
                position=gtfs.Position(
                    latitude=vehicle["lat"],
                    longitude=vehicle["lon"],
                ),
            )) for idx, (vehicle_id, vehicle) in enumerate(vehicles.items())
    ]

    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=0),
        entity=vehicles_entities + [
            gtfs.FeedEntity(
                id="trip_update_1",
                trip_update=gtfs.TripUpdate(
                    vehicle=gtfs.VehicleDescriptor(id=VEHICLE_ID_1),
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID_1,
                                             route_id=ROUTE_ID,
                                             direction_id=True),
                    stop_time_update=[
                        gtfs.TripUpdate.StopTimeUpdate(
                            arrival=gtfs.TripUpdate.StopTimeEvent(time=time),
                            departure=gtfs.TripUpdate.StopTimeEvent(time=time +
                                                                    15),
                            stop_id=stop_id,
                            stop_sequence=stop_sequence + 25,
                        ) for stop_sequence,
                        (stop_id, time) in enumerate(stop_id_to_time.items())
                    ],
                ),
            ),
            gtfs.FeedEntity(
                id="trip_update_2",
                trip_update=gtfs.TripUpdate(
                    vehicle=gtfs.VehicleDescriptor(id=VEHICLE_ID_2),
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID_2,
                                             route_id=ROUTE_ID,
                                             direction_id=True),
                ),
            ),
            gtfs.FeedEntity(
                id="trip_update_3",
                trip_update=gtfs.TripUpdate(
                    vehicle=gtfs.VehicleDescriptor(id=VEHICLE_ID_3),
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID_3,
                                             route_id=ROUTE_ID,
                                             direction_id=True),
                ),
            )
        ],
    )
