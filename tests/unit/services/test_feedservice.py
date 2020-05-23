import datetime
from unittest import mock

import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import feedqueries, systemqueries
from transiter.services import feedservice, views, updatemanager

SYSTEM_ID = "1"
FEED_ONE_ID = "2"
FEED_ONE_PK = 3
FEED_ONE_AUTO_UPDATE_PERIOD = 500
FEED_TWO_AUTO_UPDATE_PERIOD = -1
FEED_TWO_ID = "4"


@pytest.fixture
def system():
    return models.System(id=SYSTEM_ID, name="", status=None)


@pytest.fixture
def feed_1(system):
    return models.Feed(
        id=FEED_ONE_ID, auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD, system=system
    )


@pytest.fixture
def feed_2(system):
    return models.Feed(
        id=FEED_TWO_ID, auto_update_period=FEED_TWO_AUTO_UPDATE_PERIOD, system=system
    )


def test_list_all_auto_updating(monkeypatch, feed_1):
    monkeypatch.setattr(feedqueries, "list_all_auto_updating", lambda: [feed_1])

    expected = [
        views.Feed(
            id=FEED_ONE_ID,
            auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD,
            _system_id=SYSTEM_ID,
            system=views.System(id=SYSTEM_ID, name="", status=None),
        )
    ]

    actual = list(feedservice.list_all_auto_updating())

    assert expected == actual


def test_list_all_in_system__no_such_system(monkeypatch):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.list_all_in_system(SYSTEM_ID)


def test_list_all_in_system(monkeypatch, system, feed_1, feed_2):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: system)
    monkeypatch.setattr(
        feedqueries, "list_all_in_system", lambda *args: [feed_1, feed_2]
    )

    expected = [
        views.Feed(
            id=FEED_ONE_ID,
            auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD,
            _system_id=SYSTEM_ID,
        ),
        views.Feed(
            id=FEED_TWO_ID,
            auto_update_period=FEED_TWO_AUTO_UPDATE_PERIOD,
            _system_id=SYSTEM_ID,
        ),
    ]

    actual = feedservice.list_all_in_system(SYSTEM_ID)

    assert actual == expected


def test_get_in_system_by_id(monkeypatch, feed_1):
    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: feed_1)

    expected = views.FeedLarge(
        id=FEED_ONE_ID,
        auto_update_period=FEED_ONE_AUTO_UPDATE_PERIOD,
        _system_id=SYSTEM_ID,
        updates=views.UpdatesInFeedLink(_feed_id=FEED_ONE_ID, _system_id=SYSTEM_ID),
    )

    actual = feedservice.get_in_system_by_id(SYSTEM_ID, FEED_ONE_ID)

    assert expected == actual


def test_get_in_system_by_id__no_such_feed(monkeypatch):
    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.get_in_system_by_id(SYSTEM_ID, FEED_ONE_ID),


def test_create_feed_update(monkeypatch):
    feed_update = mock.MagicMock()

    monkeypatch.setattr(updatemanager, "create_feed_update", lambda *args: feed_update)
    monkeypatch.setattr(updatemanager, "execute_feed_update", mock.MagicMock())

    actual = feedservice.create_and_execute_feed_update(SYSTEM_ID, FEED_ONE_ID)

    assert feed_update == actual


def test_create_feed_update__no_such_feed(monkeypatch):
    monkeypatch.setattr(updatemanager, "create_feed_update", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.create_and_execute_feed_update(SYSTEM_ID, FEED_ONE_ID)


def test_list_updates_in_feed(monkeypatch, feed_1):
    update_1 = models.FeedUpdate(feed=feed_1)
    update_2 = models.FeedUpdate(feed=feed_1)

    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: feed_1)
    monkeypatch.setattr(
        feedqueries, "list_updates_in_feed", lambda *args: [update_1, update_2]
    )

    expected = [
        views.FeedUpdate.from_model(update_1),
        views.FeedUpdate.from_model(update_2),
    ]

    actual = feedservice.list_updates_in_feed(SYSTEM_ID, FEED_ONE_ID)

    assert expected == actual


def test_list_updates_in_feed__no_such_feed(monkeypatch):
    monkeypatch.setattr(feedqueries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        feedservice.list_updates_in_feed(SYSTEM_ID, FEED_ONE_ID)


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
