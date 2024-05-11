from . import client
from . import txtar
from . import shared


GTFS_STATIC_TXTAR = """
-- routes.txt --
route_id,route_color,route_text_color,route_short_name,route_long_name,route_desc,route_type,route_url,route_sort_order,continuous_pickup,continuous_drop_off
RouteID1,RouteColor1,RouteTextColor1,RouteShortName1,RouteLongName1,RouteDesc1,1,RouteUrl1,50,2,3
RouteID2,RouteColor2,RouteTextColor2,RouteShortName2,RouteLongName2,RouteDesc2,2,RouteUrl2,25,0,1
"""

GTFS_STATIC_TXTAR_UPDATED = """
-- routes.txt --
route_id,route_color,route_text_color,route_short_name,route_long_name,route_desc,route_type,route_url,route_sort_order,continuous_pickup,continuous_drop_off
RouteID1,RouteColor3,RouteTextColor3,RouteShortName3,RouteLongName3,RouteDesc3,3,RouteUrl3,75,3,2
"""


def test_route(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    route_1 = client.Route(
        id="RouteID1",
        url="RouteUrl1",
        color="RouteColor1",
        textColor="RouteTextColor1",
        shortName="RouteShortName1",
        longName="RouteLongName1",
        description="RouteDesc1",
        sortOrder=50,
        continuousPickup="PHONE_AGENCY",
        continuousDropOff="COORDINATE_WITH_DRIVER",
        type="SUBWAY",
        serviceMaps=[],
        alerts=[],
    )
    route_2 = client.Route(
        id="RouteID2",
        url="RouteUrl2",
        color="RouteColor2",
        textColor="RouteTextColor2",
        shortName="RouteShortName2",
        longName="RouteLongName2",
        description="RouteDesc2",
        sortOrder=25,
        continuousPickup="ALLOWED",
        continuousDropOff="NOT_ALLOWED",
        type="RAIL",
        serviceMaps=[],
        alerts=[],
    )
    install_system(system_id, GTFS_STATIC_TXTAR)

    got_system = transiter_client.get_system(system_id)
    assert got_system.routes == client.ChildResources(
        count=2, path=f"systems/{system_id}/routes"
    )

    # We skip service maps because those are tested in their own test.
    params = {"skip_service_maps": "true"}

    got_list_routes = transiter_client.list_routes(system_id, params)
    assert got_list_routes.routes == [route_1, route_2]

    got_route = transiter_client.get_route(system_id, "RouteID1", params)
    assert got_route == route_1


def test_update(
    system_id,
    install_system,
    source_server,
    transiter_client: client.TransiterClient,
):
    route_1 = client.Route(
        id="RouteID1",
        url="RouteUrl3",
        color="RouteColor3",
        textColor="RouteTextColor3",
        shortName="RouteShortName3",
        longName="RouteLongName3",
        description="RouteDesc3",
        sortOrder=75,
        continuousPickup="COORDINATE_WITH_DRIVER",
        continuousDropOff="PHONE_AGENCY",
        type="BUS",
        serviceMaps=[],
        alerts=[],
    )
    static_feed_url, _ = install_system(system_id, GTFS_STATIC_TXTAR)
    source_server.put(
        static_feed_url,
        txtar.to_zip(shared.GTFS_STATIC_DEFAULT_TXTAR + GTFS_STATIC_TXTAR_UPDATED),
    )
    transiter_client.perform_feed_update(system_id, shared.GTFS_STATIC_FEED_ID)

    # We skip service maps because those are tested in their own test.
    params = {"skip_service_maps": "true"}

    got_list_routes = transiter_client.list_routes(system_id, params)
    assert got_list_routes.routes == [route_1]
