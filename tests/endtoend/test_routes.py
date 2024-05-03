from . import client


ROUTE_IDS = {"A", "B", "RouteID"}


def test_route(
    system_id,
    install_system_1,
    transiter_client: client.TransiterClient,
):
    install_system_1(system_id)

    got_system = transiter_client.get_system(system_id)
    assert got_system.routes.count == len(ROUTE_IDS)

    got_list_routes = transiter_client.list_routes(system_id)
    got_route_ids = set([route.id for route in got_list_routes.routes])
    assert got_route_ids == ROUTE_IDS

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
    # We skip service maps because those are tested in their own test.
    params = {"skip_service_maps": "true"}
    got_route = transiter_client.get_route(system_id, "RouteID", params)
    assert got_route == want_route
