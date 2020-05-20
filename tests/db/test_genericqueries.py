from transiter import models
from transiter.data import genericqueries, routequeries


def test_get_id_to_pk_map_by_feed_pk(
    db_session, add_model, feed_1_1, feed_1_2, route_1_1, route_1_2, route_1_3
):
    update_1 = add_model(models.FeedUpdate(feed=feed_1_1))
    update_2 = add_model(models.FeedUpdate(feed=feed_1_2))
    route_1_1.source = update_1
    route_1_2.source = update_2
    route_1_3.source = update_2
    db_session.flush()

    expected = {
        route_1_2.id: route_1_2.pk,
        route_1_3.id: route_1_3.pk,
    }

    actual = genericqueries.get_id_to_pk_map_by_feed_pk(models.Route, feed_1_2.pk)

    assert expected == actual


def test_get_id_to_pk_map_by_feed_pk__no_matches(
    db_session, add_model, feed_1_1, feed_1_2,
):
    update_1 = add_model(models.FeedUpdate(feed=feed_1_1))
    update_2 = add_model(models.FeedUpdate(feed=feed_1_2))
    db_session.flush()

    expected = {}

    actual = genericqueries.get_id_to_pk_map_by_feed_pk(models.Route, feed_1_2.pk)

    assert expected == actual


def test_delete_stale_entities(
    db_session, add_model, system_1, feed_1_1, route_1_1, route_1_2, route_1_3
):
    # This breaks the test and hence the method:
    # add_model(models.Trip(route=route_1_1))
    update_1 = add_model(models.FeedUpdate(feed=feed_1_1))
    update_2 = add_model(models.FeedUpdate(feed=feed_1_1))
    route_1_1.source = update_1
    route_1_2.source = update_2
    route_1_3.source = update_2
    db_session.flush()

    genericqueries.delete_stale_entities(models.Route, update_2)

    assert [route_1_2, route_1_3] == routequeries.list_in_system(system_1.id)


def test_list_stale_entities(
    db_session, add_model, feed_1_1, route_1_1, route_1_2, route_1_3
):
    update_1 = add_model(models.FeedUpdate(feed=feed_1_1))
    update_2 = add_model(models.FeedUpdate(feed=feed_1_1))
    route_1_1.source = update_1
    route_1_2.source = update_2
    route_1_3.source = update_2
    db_session.flush()

    assert [route_1_1] == genericqueries.list_stale_entities(models.Route, update_2)


def test_count_number_of_related_entities(system_1, route_1_1, route_1_2, route_2_1):
    assert 2 == genericqueries.count_number_of_related_entities(
        models.System.routes, system_1
    )


def test_count_number_of_related_entities__none(system_1, route_2_1):
    assert 0 == genericqueries.count_number_of_related_entities(
        models.System.routes, system_1
    )
