import pytest
import requests
from . import gtfs_realtime_pb2 as gtfs
from haversine import haversine

SHAPE_ID_1 = "shape_1"
SHAPE_ID_2 = "shape_2"
SHAPE_ID_3 = "shape_3"
TRIP_ID_1 = "trip_id_1"
ROUTE_ID = "A"


class TestShapes:

    def test_shape_view(self, install_system_1, system_id, transiter_host,
                        source_server):
        __, realtime_feed_url = install_system_1(
            system_id, only_process_full_entities="true")

        source_server.put(
            realtime_feed_url,
            build_gtfs_rt_message().SerializeToString(),
        )
        response = requests.post(
            f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed"
        ).json()
        print(response)

        # List shapes
        response = requests.get(
            f"{transiter_host}/systems/{system_id}/shapes").json()
        print(response)

        shapes = response["shapes"]
        assert 3 == len(shapes)
        assert_shape_1(shapes[0])
        assert_shape_2(shapes[1])
        assert_shape_3(shapes[2])

        # List shapes (pagination)
        paginated_shapes = []
        next_id = None
        num_pages = 0
        while len(paginated_shapes) < len(shapes):
            query_params = {
                "limit": 2,
            }
            if next_id:
                query_params["first_id"] = next_id
            response = requests.get(
                f"{transiter_host}/systems/{system_id}/shapes",
                params=query_params).json()
            assert len(response["shapes"]) <= 2
            paginated_shapes.extend(response["shapes"])
            num_pages += 1

            if "nextId" not in response:
                break
            next_id = response["nextId"]
        assert {SHAPE_ID_1, SHAPE_ID_2,
                SHAPE_ID_3} == set(shape["id"] for shape in paginated_shapes)
        assert num_pages == 2

        # List shapes by ids
        query_params = {
            "only_return_specified_ids": True,
            "id[]": [SHAPE_ID_1, SHAPE_ID_3],
        }
        response = requests.get(f"{transiter_host}/systems/{system_id}/shapes",
                                params=query_params).json()
        print(response)
        assert {SHAPE_ID_1,
                SHAPE_ID_3} == set(shape["id"] for shape in response["shapes"])

        # Get shape
        response = requests.get(
            f"{transiter_host}/systems/{system_id}/shapes/{SHAPE_ID_1}").json(
            )
        print(response)
        assert_shape_1(response)

        response = requests.get(
            f"{transiter_host}/systems/{system_id}/shapes/{SHAPE_ID_2}").json(
            )
        print(response)
        assert_shape_2(response)

    def test_trip_view(self, install_system_1, system_id, transiter_host,
                       source_server):
        __, realtime_feed_url = install_system_1(
            system_id, only_process_full_entities="true")

        source_server.put(
            realtime_feed_url,
            build_gtfs_rt_message().SerializeToString(),
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
        assert response["shape"]["id"] == SHAPE_ID_1


def assert_shape_1(shape):
    assert shape["id"] == SHAPE_ID_1
    assert shape["points"] == [
        {
            "latitude": 100,
            "longitude": 200,
        },
        {
            "latitude": 150,
            "longitude": 250,
        },
        {
            "latitude": 200,
            "longitude": 300,
        },
    ]


def assert_shape_2(shape):
    assert shape["id"] == SHAPE_ID_2
    assert shape["points"] == [
        {
            "latitude": 200,
            "longitude": 300,
        },
        {
            "latitude": 250,
            "longitude": 350,
        },
        {
            "latitude": 300,
            "longitude": 400,
        },
    ]


def assert_shape_3(shape):
    assert shape["id"] == SHAPE_ID_3
    assert shape["points"] == [
        {
            "latitude": -10,
            "longitude": -20,
        },
    ]


def build_gtfs_rt_message():
    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=0),
        entity=[
            gtfs.FeedEntity(
                id="trip_update_1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID_1,
                                             route_id=ROUTE_ID,
                                             direction_id=True), ),
            ),
        ],
    )
