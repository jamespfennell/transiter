import pytest

from transiter.db import models
from transiter.db.queries import servicemapqueries


@pytest.fixture
def service_map_group_1(add_model, system_1):
    return add_model(
        models.ServiceMapGroup(
            system=system_1,
            source=models.ServiceMapGroup.ServiceMapSource.REALTIME,
            use_for_routes_at_stop=True,
            pk=501,
            id="502",
        )
    )


@pytest.fixture
def service_map_group_2(add_model, system_1):
    return add_model(
        models.ServiceMapGroup(
            system=system_1,
            source=models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
            use_for_stops_in_route=True,
            pk=503,
            id="504",
        )
    )


@pytest.fixture
def service_map_1_1(add_model, route_1_1, stop_1_1, stop_1_2, service_map_group_1):
    return add_model(
        models.ServiceMap(
            group=service_map_group_1,
            route=route_1_1,
            pk=521,
            vertices=[
                models.ServiceMapVertex(stop=stop_1_1),
                models.ServiceMapVertex(stop=stop_1_2),
            ],
        )
    )


@pytest.fixture
def service_map_1_2(add_model, route_1_2, stop_1_2, stop_1_3, service_map_group_1):
    return add_model(
        models.ServiceMap(
            group=service_map_group_1,
            route=route_1_2,
            pk=523,
            vertices=[
                models.ServiceMapVertex(stop=stop_1_2),
                models.ServiceMapVertex(stop=stop_1_3),
            ],
        )
    )


@pytest.fixture
def service_map_2_1(add_model, route_1_2, stop_1_1, stop_1_2, service_map_group_2):
    return add_model(
        models.ServiceMap(
            group=service_map_group_2,
            route=route_1_2,
            pk=525,
            vertices=[
                models.ServiceMapVertex(stop=stop_1_1),
                models.ServiceMapVertex(stop=stop_1_2),
            ],
        )
    )


def test_list_groups_and_maps_for_stops_in_route(
    route_1_2,
    service_map_group_1,
    service_map_group_2,
    service_map_1_1,
    service_map_1_2,
    service_map_2_1,
):
    expected = [
        (service_map_group_2, service_map_2_1),
    ]

    actual = servicemapqueries.list_groups_and_maps_for_stops_in_route(route_1_2.pk)

    assert expected == actual


def test_list_groups_and_maps_for_stops_in_route__none(
    route_1_3,
    service_map_group_1,
    service_map_group_2,
    service_map_1_1,
    service_map_1_2,
    service_map_2_1,
):
    expected = [
        (service_map_group_2, None),
    ]

    actual = servicemapqueries.list_groups_and_maps_for_stops_in_route(route_1_3.pk)

    assert expected == actual


def test_get_stop_pk_to_group_id_to_routes_map(
    stop_1_1,
    stop_1_2,
    stop_1_3,
    stop_1_4,
    stop_1_5,
    service_map_group_1,
    service_map_1_1,
    service_map_1_2,
    route_1_1,
    route_1_2,
):
    expected = {
        stop_1_1.pk: {service_map_group_1.id: [route_1_1]},
        stop_1_2.pk: {service_map_group_1.id: [route_1_1, route_1_2]},
        stop_1_3.pk: {service_map_group_1.id: [route_1_2]},
        stop_1_4.pk: {service_map_group_1.id: []},
        stop_1_5.pk: {service_map_group_1.id: []},
    }

    actual = servicemapqueries.get_stop_pk_to_group_id_to_routes_map(
        [stop_1_1.pk, stop_1_2.pk, stop_1_3.pk, stop_1_4.pk, stop_1_5.pk]
    )

    assert expected == actual
