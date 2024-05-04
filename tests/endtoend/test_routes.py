from . import client


def test_route(
    system_id,
    install_system_using_txtar,
    transiter_client: client.TransiterClient,
):
    gtfs_static_txtar = """
    -- routes.txt --
    route_id,route_color,route_text_color,route_short_name,route_long_name,route_desc,route_type,route_url,route_sort_order,continuous_pickup,continuous_drop_off
    RouteID,RouteColor,RouteTextColor,RouteShortName,RouteLongName,RouteDesc,1,RouteUrl,50,2,3
    """
    want_route = client.Route(
        id="RouteID",
        url="RouteUrl",
        color="RouteColor",
        textColor="RouteTextColor",
        shortName="RouteShortName",
        longName="RouteLongName",
        description="RouteDesc",
        sortOrder=50,
        continuousPickup="PHONE_AGENCY",
        continuousDropOff="COORDINATE_WITH_DRIVER",
        type="SUBWAY",
        serviceMaps=[],
    )
    install_system_using_txtar(system_id, gtfs_static_txtar)

    got_system = transiter_client.get_system(system_id)
    assert got_system.routes == client.ChildResources(
        count=1, path=f"systems/{system_id}/routes"
    )

    # We skip service maps because those are tested in their own test.
    params = {"skip_service_maps": "true"}

    got_list_routes = transiter_client.list_routes(system_id, params)
    assert got_list_routes.routes == [want_route]

    got_route = transiter_client.get_route(system_id, "RouteID", params)
    assert got_route == want_route
