import shared
from . import gtfs_realtime_pb2 as gtfs
from . import client

SHAPE_1 = client.Shape(
    id="shape_1",
    points=[
        client.ShapePoint(latitude=100, longitude=200, distance=None),
        client.ShapePoint(latitude=150, longitude=250, distance=None),
        client.ShapePoint(latitude=200, longitude=300, distance=None),
    ],
)

SHAPE_2 = client.Shape(
    id="shape_2",
    points=[
        client.ShapePoint(latitude=200, longitude=300, distance=None),
        client.ShapePoint(latitude=250, longitude=350, distance=None),
        client.ShapePoint(latitude=300, longitude=400, distance=None),
    ],
)


SHAPE_3 = client.Shape(
    id="shape_3",
    points=[
        client.ShapePoint(latitude=-10, longitude=-20, distance=None),
    ],
)

TRIP_ID = "trip_id_1"
ROUTE_ID = "A"


GTFS_STATIC_TXTAR = f"""
-- routes.txt --
route_id,route_type
{ROUTE_ID},2
-- shapes.txt --
shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence
{SHAPE_1.id},100,200,0
{SHAPE_1.id},150,250,1
{SHAPE_1.id},200,300,2
{SHAPE_2.id},200,300,0
{SHAPE_2.id},250,350,1
{SHAPE_2.id},300,400,2
{SHAPE_3.id},-10,-20,0
-- calendar.txt --
service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
Weekday,1,1,1,1,1,0,0,20180101,20181231
-- trips.txt --
route_id,service_id,trip_id,direction_id,shape_id
{ROUTE_ID},Weekday,{TRIP_ID},1,{SHAPE_1.id}
"""


def test_list_shapes(
    install_system_using_txtar,
    system_id,
    transiter_client: client.TransiterClient,
):
    install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)

    got_list_shapes = transiter_client.list_shapes(system_id)
    assert got_list_shapes.shapes == [SHAPE_1, SHAPE_2, SHAPE_3]


def test_list_shapes_with_pagination(
    install_system_using_txtar,
    system_id,
    transiter_client: client.TransiterClient,
):
    install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)

    got_list_shapes = transiter_client.list_shapes(
        system_id,
        params={
            "limit": 2,
        },
    )
    assert got_list_shapes == client.ListShapesResponse(
        shapes=[SHAPE_1, SHAPE_2],
        nextId=SHAPE_3.id,
    )

    got_list_shapes = transiter_client.list_shapes(
        system_id,
        params={
            "limit": 2,
            "first_id": got_list_shapes.nextId,
        },
    )
    assert got_list_shapes == client.ListShapesResponse(
        shapes=[SHAPE_3],
        nextId=None,
    )


def test_list_shapes_with_filtering(
    install_system_using_txtar,
    system_id,
    transiter_client: client.TransiterClient,
):
    install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)
    got_list_shapes = transiter_client.list_shapes(
        system_id,
        params={
            "filter_by_id": True,
            "id[]": [SHAPE_1.id, SHAPE_3.id],
        },
    )
    assert got_list_shapes.shapes == [SHAPE_1, SHAPE_3]


def test_get_shape(
    install_system_using_txtar,
    system_id,
    transiter_client: client.TransiterClient,
):
    install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)

    for want_shape in [SHAPE_1, SHAPE_2, SHAPE_3]:
        got_shape = transiter_client.get_shape(system_id, want_shape.id)
        assert got_shape == want_shape


def test_trip_view(
    install_system_using_txtar,
    system_id,
    transiter_client: client.TransiterClient,
    source_server: shared.SourceServerClient,
):
    __, realtime_feed_url = install_system_using_txtar(system_id, GTFS_STATIC_TXTAR)

    gtfs_rt_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=0),
        entity=[
            gtfs.FeedEntity(
                id="trip_update_1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(
                        trip_id=TRIP_ID, route_id=ROUTE_ID, direction_id=True
                    ),
                ),
            ),
        ],
    )
    source_server.put(
        realtime_feed_url,
        gtfs_rt_message.SerializeToString(),
    )
    transiter_client.perform_feed_update(system_id, shared.GTFS_REALTIME_FEED_ID)

    trip = transiter_client.get_trip(system_id, ROUTE_ID, TRIP_ID)
    assert trip.shape == client.ShapeReference(id=SHAPE_1.id)
