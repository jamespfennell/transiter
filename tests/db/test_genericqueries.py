import pytest

from transiter import models
from transiter.data.dams import servicemapdam
from transiter import models
from transiter.data.dams import genericqueries


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
