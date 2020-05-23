from transiter.db.queries import routequeries


def test_list_all_in_system(system_1, route_1_1, route_1_2, route_2_1):
    assert [route_1_1, route_1_2] == (routequeries.list_in_system(system_1.id))


def test_list_all_in_system__empty(system_1, route_2_1):
    assert [] == (routequeries.list_in_system(system_1.id))


def test_get_in_system_by_id(system_1, route_1_1):
    assert route_1_1 == (routequeries.get_in_system_by_id(system_1.id, route_1_1.id))


def test_get_in_system_by_id__none(system_2, route_1_1):
    assert None is (routequeries.get_in_system_by_id(system_2.id, route_1_1.id))


def test_get_id_to_pk_map_in_system(system_1, route_1_1, route_1_2, route_2_1):
    expected = {
        route_1_1.id: route_1_1.pk,
        route_1_2.id: route_1_2.pk,
        route_2_1.id: None,
        "unknown": None,
    }

    actual = routequeries.get_id_to_pk_map_in_system(system_1.pk, expected.keys())

    assert expected == actual


def test_get_id_to_pk_map_in_system__all_routes(
    system_1, route_1_1, route_1_2, route_2_1
):
    expected = {
        route_1_1.id: route_1_1.pk,
        route_1_2.id: route_1_2.pk,
    }

    actual = routequeries.get_id_to_pk_map_in_system(system_1.pk)

    assert expected == actual


def test_calculate_periodicity(route_1_1, trip_1, trip_2, trip_3):
    assert 3600 == routequeries.calculate_periodicity(route_1_1.pk)


def test_calculate_periodicity__no_trips(route_1_1,):
    assert None is routequeries.calculate_periodicity(route_1_1.pk)


def test_calculate_periodicity__one_trips(route_1_1, trip_1):
    assert None is routequeries.calculate_periodicity(route_1_1.pk)


def test_list_route_pks_with_current_service(route_1_1, route_1_2, route_1_3, trip_1):
    assert [route_1_1.pk] == routequeries.list_route_pks_with_current_service(
        [route_1_1.pk, route_1_2.pk, route_1_3.pk]
    )


def test_list_route_pks_with_current_service__no_service(
    route_1_1, route_1_2, route_1_3
):
    assert [] == routequeries.list_route_pks_with_current_service(
        [route_1_1.pk, route_1_2.pk, route_1_3.pk]
    )


def test_list_route_pks_with_current_service__no_inputs(
    route_1_1, route_1_2, route_1_3
):
    assert [] == routequeries.list_route_pks_with_current_service([])
