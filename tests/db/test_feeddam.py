import datetime

from transiter import models
from transiter.data.dams import feeddam


def test_list_all_feed_pks(feed_1_1, feed_1_2, feed_2_1):
    expected_pks = set(feed.pk for feed in [feed_1_1, feed_1_2, feed_2_1])

    actual_pks = set(feeddam.list_all_feed_pks())

    assert expected_pks == actual_pks


def test_list_all_auto_updating(feed_1_1, feed_1_2, feed_2_1):
    assert [feed_1_1, feed_2_1] == feeddam.list_all_auto_updating()


def test_list_all_auto_updating__system_off(
    db_session, system_1, feed_1_1, feed_1_2, feed_2_1
):
    system_1.auto_update_enabled = False
    db_session.flush()

    assert [feed_2_1] == feeddam.list_all_auto_updating()


def test_list_all_auto_updating__system_not_active(
    db_session, system_1, feed_1_1, feed_1_2, feed_2_1
):
    system_1.status = models.System.SystemStatus.INSTALLING
    db_session.flush()

    assert [feed_2_1] == feeddam.list_all_auto_updating()


def test_list_all_in_system(system_1, feed_1_1, feed_1_2, feed_2_1):
    assert [feed_1_1, feed_1_2] == feeddam.list_all_in_system(system_1.id)


def test_list_all_in_system__no_feeds(system_1, feed_2_1):
    assert [] == feeddam.list_all_in_system(system_1.id)


def test_get_in_system_by_id(system_1, feed_1_1):
    assert feed_1_1 == feeddam.get_in_system_by_id(system_1.id, feed_1_1.id)


def test_get_in_system_by_id__no_feed(system_1, feed_1_1):
    assert None is feeddam.get_in_system_by_id(system_1.id, "unknown_id")


def test_get_in_system_by_id__no_system(system_1, feed_1_1):
    assert None is feeddam.get_in_system_by_id("unknown_id", feed_1_1.id)


def test_get_update_by_pk(feed_1_1_update_1):
    assert feed_1_1_update_1 == feeddam.get_update_by_pk(feed_1_1_update_1.pk)


def test_get_update_by_pk__unknown_pk(feed_1_1_update_1):
    assert None is feeddam.get_update_by_pk(1)


def test_get_last_successful_update(
    feed_1_1, feed_1_1_update_1, feed_1_1_update_2, feed_1_1_update_3
):
    assert feed_1_1_update_2.content_hash == feeddam.get_last_successful_update_hash(
        feed_1_1.pk
    )


def test_get_last_successful_update__no_update(feed_1_1):
    assert None is feeddam.get_last_successful_update_hash(feed_1_1.pk)


def test_list_updates_in_feed(
    feed_1_1, feed_1_1_update_1, feed_1_1_update_2, feed_1_1_update_3
):
    assert [
        feed_1_1_update_3,
        feed_1_1_update_2,
        feed_1_1_update_1,
    ] == feeddam.list_updates_in_feed(feed_1_1.pk)


def test_list_updates_in_feed__no_updates(feed_1_1):
    assert [] == feeddam.list_updates_in_feed(feed_1_1.pk)


def test_trim_feed_updates__all_trimmed(
    db_session, feed_1_1, feed_1_1_update_1, feed_1_1_update_2, feed_1_1_update_3
):
    feeddam.trim_feed_updates(feed_1_1.pk, datetime.datetime(2018, 1, 1, 2, 0, 0))

    assert [] == feeddam.list_updates_in_feed(feed_1_1.pk)


def test_trim_feed_updates__some_after_date(
    feed_1_1, feed_1_1_update_1, feed_1_1_update_2, feed_1_1_update_3
):
    feeddam.trim_feed_updates(feed_1_1.pk, datetime.datetime(2011, 1, 1, 4, 0, 0))

    assert [feed_1_1_update_3] == feeddam.list_updates_in_feed(feed_1_1.pk)


def test_trim_feed_updates__some_still_used_as_source(
    db_session,
    feed_1_1,
    feed_1_1_update_1,
    feed_1_1_update_2,
    feed_1_1_update_3,
    route_1_1,
):
    route_1_1.source = feed_1_1_update_2
    db_session.flush()

    feeddam.trim_feed_updates(feed_1_1.pk, datetime.datetime(2018, 1, 1, 2, 0, 0))

    assert [feed_1_1_update_2] == feeddam.list_updates_in_feed(feed_1_1.pk)


def test__delete_in_system_by_id(db_session, system_1, feed_1_1):
    response = feeddam.delete_in_system_by_id(system_1.id, feed_1_1.id)

    assert response is True
    assert [] == db_session.query(models.Feed).all()


def test__delete_in_system_by_id__unknown_feed(db_session, system_1, feed_1_1):
    response = feeddam.delete_in_system_by_id(system_1.id, "unknown")

    assert response is False
    assert [feed_1_1] == db_session.query(models.Feed).all()
