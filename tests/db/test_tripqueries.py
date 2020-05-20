from transiter import models
from transiter.data import tripqueries


def test_list_all_from_feed(
    db_session, add_model, feed_1_1, feed_1_2, trip_1, trip_2, trip_3
):
    feed_update_1_1 = add_model(models.FeedUpdate(feed=feed_1_1))
    feed_update_1_2 = add_model(models.FeedUpdate(feed=feed_1_2))
    trip_1.source = feed_update_1_1
    trip_2.source = feed_update_1_1
    trip_3.source = feed_update_1_2
    db_session.flush()

    assert [trip_1, trip_2] == tripqueries.list_all_from_feed(feed_1_1.pk)


def test_list_all_in_route(route_1_1, trip_1, trip_2, trip_3):
    assert [trip_1, trip_2, trip_3] == tripqueries.list_all_in_route_by_pk(route_1_1.pk)


def test_list_all_in_route__no_trips(route_1_1, route_1_2):
    assert [] == tripqueries.list_all_in_route_by_pk(route_1_2.pk)


def test_get_in_route_by_id(system_1, route_1_1, trip_1):
    assert trip_1 == tripqueries.get_in_route_by_id(
        system_1.id, route_1_1.id, trip_1.id
    )


def test_get_in_route_by_id__no_system(system_1, route_1_1, trip_1):
    assert None is tripqueries.get_in_route_by_id("unknown_id", route_1_1.id, trip_1.id)


def test_get_in_route_by_id__no_route(system_1, route_1_1, trip_1):
    assert None is tripqueries.get_in_route_by_id(system_1.id, "unknown_id", trip_1.id)


def test_get_in_route_by_id__no_trip(system_1, route_1_1, trip_1):
    assert None is tripqueries.get_in_route_by_id(
        system_1.id, route_1_1.id, "unknown_id"
    )


def test_get_trip_pk_to_last_stop_map(route_1_1, stop_1_4, trip_1, trip_2, trip_3):
    expected = {
        trip_1.pk: stop_1_4,
        trip_2.pk: stop_1_4,
        trip_3.pk: stop_1_4,
    }

    actual = tripqueries.get_trip_pk_to_last_stop_map(expected.keys())

    assert expected == actual


def test_get_trip_pk_to_path_map(
    route_1_1, stop_1_1, stop_1_2, stop_1_3, stop_1_4, trip_1, trip_2, trip_3
):
    expected = {
        trip_1.pk: [stop_1_1.pk, stop_1_2.pk, stop_1_3.pk, stop_1_4.pk],
        trip_2.pk: [stop_1_1.pk, stop_1_2.pk, stop_1_4.pk],
        trip_3.pk: [stop_1_1.pk, stop_1_4.pk],
    }

    actual = tripqueries.get_trip_pk_to_path_map(route_1_1.pk)

    assert expected == actual


def test_list_by_system_and_trip_ids(
    add_model, system_1, route_1_1, route_2_1, trip_1, trip_2, trip_3
):
    other_system_trip = add_model(models.Trip(id=trip_1.id, route=route_2_1))

    actual = tripqueries.list_by_system_and_trip_ids(
        system_1.id, [trip_1.id, trip_2.id]
    )

    assert [trip_1, trip_2] == actual
