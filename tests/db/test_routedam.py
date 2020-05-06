from transiter import models
from transiter.data.dams import routedam


def test_list_all_in_system(system_1, route_1_1, route_1_2, route_2_1):
    assert [route_1_1, route_1_2] == (routedam.list_all_in_system(system_1.id))


def test_list_all_in_system__empty(system_1, route_2_1):
    assert [] == (routedam.list_all_in_system(system_1.id))


def test_get_in_system_by_id(system_1, route_1_1):
    assert route_1_1 == (routedam.get_in_system_by_id(system_1.id, route_1_1.id))


def test_get_in_system_by_id__none(system_2, route_1_1):
    assert None is (routedam.get_in_system_by_id(system_2.id, route_1_1.id))


def test_get_id_to_pk_map_in_system(system_1, route_1_1, route_1_2, route_2_1):
    expected = {
        route_1_1.id: route_1_1.pk,
        route_1_2.id: route_1_2.pk,
        route_2_1.id: None,
        "unknown": None,
    }

    actual = routedam.get_id_to_pk_map_in_system(system_1.pk, expected.keys())

    assert expected == actual


def test_get_id_to_pk_map_in_system__all_routes(
    system_1, route_1_1, route_1_2, route_2_1
):
    expected = {
        route_1_1.id: route_1_1.pk,
        route_1_2.id: route_1_2.pk,
    }

    actual = routedam.get_id_to_pk_map_in_system(system_1.pk)

    assert expected == actual


def test_calculate_periodicity(route_1_1, trip_1, trip_2, trip_3):
    assert 3600 == routedam.calculate_periodicity(route_1_1.pk)


def test_calculate_periodicity__no_trips(route_1_1,):
    assert None is routedam.calculate_periodicity(route_1_1.pk)


def test_calculate_periodicity__one_trips(route_1_1, trip_1):
    assert None is routedam.calculate_periodicity(route_1_1.pk)


def test_list_route_pks_with_current_service(route_1_1, route_1_2, route_1_3, trip_1):
    assert [route_1_1.pk] == routedam.list_route_pks_with_current_service(
        [route_1_1.pk, route_1_2.pk, route_1_3.pk]
    )


def test_list_route_pks_with_current_service__no_service(
    route_1_1, route_1_2, route_1_3
):
    assert [] == routedam.list_route_pks_with_current_service(
        [route_1_1.pk, route_1_2.pk, route_1_3.pk]
    )


def test_list_route_pks_with_current_service__no_inputs(
    route_1_1, route_1_2, route_1_3
):
    assert [] == routedam.list_route_pks_with_current_service([])


def test_get_route_pk_to_highest_priority_alerts_maps(
    db_session, add_model, route_1_1, route_1_2, route_1_3
):
    alert_1 = add_model(models.Alert(pk=701, priority=1))
    alert_2 = add_model(models.Alert(pk=702, priority=2))
    alert_3 = add_model(models.Alert(pk=703, priority=2))
    alert_4 = add_model(models.Alert(pk=704, priority=3))
    route_1_1.alerts = [alert_1, alert_2, alert_3]
    route_1_2.alerts = [alert_1, alert_3, alert_4]
    db_session.flush()

    expected = {
        route_1_1.pk: [alert_2, alert_3],
        route_1_2.pk: [alert_4],
        route_1_3.pk: [],
    }

    actual = routedam.get_route_pk_to_highest_priority_alerts_map(
        [route_1_1.pk, route_1_2.pk, route_1_3.pk]
    )

    assert expected == actual
