import datetime
from unittest import mock

import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import feedqueries, systemqueries
from transiter.services import feedservice, views, updatemanager


def test_list_all_auto_updating(
    monkeypatch, feed_1_model, feed_1_small_view, system_1_view
):
    monkeypatch.setattr(feedqueries, "list_all_auto_updating", lambda: [feed_1_model])

    feed_1_small_view.system = system_1_view

    actual = list(feedservice.list_all_auto_updating())

    assert [feed_1_small_view] == actual


def test_list_all_in_system__no_such_system(monkeypatch, system_1_model):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.list_all_in_system(system_1_model)


def test_list_all_in_system(
    monkeypatch,
    system_1_model,
    feed_1_model,
    feed_1_small_view,
    feed_2_model,
    feed_2_small_view,
):
    monkeypatch.setattr(
        systemqueries, "get_by_id", lambda *args, **kwargs: system_1_model
    )
    monkeypatch.setattr(
        feedqueries, "list_all_in_system", lambda *args: [feed_1_model, feed_2_model]
    )

    expected = [feed_1_small_view, feed_2_small_view]

    actual = feedservice.list_all_in_system(system_1_model.id)

    assert actual == expected


def test_get_in_system_by_id(monkeypatch, feed_1_model, feed_1_large_view):
    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: feed_1_model)

    actual = feedservice.get_in_system_by_id(feed_1_model.system.id, feed_1_model.id)

    assert feed_1_large_view == actual


def test_get_in_system_by_id__no_such_feed(monkeypatch, feed_1_model):
    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.get_in_system_by_id(feed_1_model.system.id, feed_1_model.id)


def test_create_feed_update(monkeypatch, feed_1_model):
    feed_update = mock.MagicMock()

    monkeypatch.setattr(updatemanager, "create_feed_update", lambda *args: feed_update)
    monkeypatch.setattr(updatemanager, "execute_feed_update", mock.MagicMock())

    actual = feedservice.create_and_execute_feed_update(
        feed_1_model.system.id, feed_1_model.id
    )

    assert feed_update == actual


def test_create_feed_update__no_such_feed(monkeypatch, feed_1_model):
    monkeypatch.setattr(updatemanager, "create_feed_update", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.create_and_execute_feed_update(
            feed_1_model.system.id, feed_1_model.id
        )


def test_list_updates_in_feed(monkeypatch, feed_1_model):
    update_1 = models.FeedUpdate(feed=feed_1_model)
    update_2 = models.FeedUpdate(feed=feed_1_model)

    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: feed_1_model)
    monkeypatch.setattr(
        feedqueries, "list_updates_in_feed", lambda *args: [update_1, update_2]
    )

    expected = [
        views.FeedUpdate.from_model(update_1),
        views.FeedUpdate.from_model(update_2),
    ]

    actual = feedservice.list_updates_in_feed(feed_1_model.system.id, feed_1_model.id)

    assert expected == actual


def test_list_updates_in_feed__no_such_feed(monkeypatch, feed_1_model):
    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.list_updates_in_feed(feed_1_model.system.id, feed_1_model.id)


@pytest.mark.parametrize(
    "feed_pks", [pytest.param([]), pytest.param([1]), pytest.param([1, 2])],
)
def test_trip_feed_updates(monkeypatch, datetime_now, feed_pks):

    before_datetime = datetime.datetime(
        year=datetime_now.year,
        month=datetime_now.month,
        day=datetime_now.day,
        hour=datetime_now.hour - 1,
        minute=datetime_now.minute,
        second=0,
        microsecond=0,
    )

    dam_trip_feed_updates = mock.Mock()
    monkeypatch.setattr(feedqueries, "list_all_feed_pks", lambda: feed_pks)
    monkeypatch.setattr(feedqueries, "trim_feed_updates", dam_trip_feed_updates)

    feedservice.trim_feed_updates()

    if len(feed_pks) == 0:
        dam_trip_feed_updates.assert_not_called()
    else:
        dam_trip_feed_updates.assert_has_calls(
            [mock.call(feed_pk, before_datetime) for feed_pk in feed_pks]
        )
