import builtins
import datetime
import random
import time
from unittest import mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from transiter.scheduler import server
from transiter.services import feedservice, views

SYSTEM_ID = "1"
FEED_ID = "2"


@pytest.fixture
def scheduler(monkeypatch):
    scheduler = mock.MagicMock()
    monkeypatch.setattr(server, "scheduler", scheduler)
    return scheduler


def test_transiter_registry(scheduler):

    server.transiter_registry.refresh()

    scheduler.add_job.assert_called_once_with(
        server.transiter_registry.all_tasks()[0].run,
        **server.CronSchedule(minute="*/15").job_kwargs()
    )


feed_1 = views.Feed(
    id=FEED_ID,
    auto_update_period=5,
    _system_id=SYSTEM_ID,
    system=views.System(id=SYSTEM_ID, name="", status=None),
)

feed_2 = views.Feed(
    id=FEED_ID,
    auto_update_period=10,
    _system_id=SYSTEM_ID,
    system=views.System(id=SYSTEM_ID, name="", status=None),
)


@pytest.mark.parametrize(
    "existing_feeds,new_feeds,job_added,job_removed",
    [
        [[], [feed_1], True, False],
        [[feed_1], [feed_1], False, False],
        [[feed_1], [feed_2], True, True],
        [[feed_1], [], False, True],
    ],
)
def test_refresh_feed_auto_update_registry(
    monkeypatch, scheduler, existing_feeds, new_feeds, job_added, job_removed
):
    mocked_datetime_class = mock.MagicMock()
    mocked_datetime_class.now.return_value = datetime.datetime.now()
    monkeypatch.setattr(datetime, "datetime", mocked_datetime_class)
    monkeypatch.setattr(random, "uniform", lambda a, b: a)

    monkeypatch.setattr(feedservice, "list_all_auto_updating", lambda: existing_feeds)

    registry = server.FeedAutoUpdateRegistry()
    registry.refresh()

    existing_job = mock.MagicMock()
    if len(list(registry.all_tasks())) > 0:
        list(registry.all_tasks())[0]._job = existing_job

    monkeypatch.setattr(feedservice, "list_all_auto_updating", lambda: new_feeds)

    scheduler.reset_mock()
    registry.refresh()

    if job_added:
        scheduler.add_job.assert_called_once()
    else:
        scheduler.add_job.assert_not_called()

    if job_removed:
        existing_job.remove.assert_called_once()
    else:
        existing_job.remove.assert_not_called()

    assert len(new_feeds) == len(list(registry.all_tasks()))


class DummyRegistry(server.Registry):
    def __init__(self):
        self.refresh = mock.MagicMock()

    def all_tasks(self):
        return []


@pytest.mark.parametrize(
    "refresh_side_effect, num_expected_refresh_calls, expect_exit_call",
    [
        [None, 1, False],  # Regular case
        [[SQLAlchemyError, None], 2, False],  # SQLAlchemy error case
        [ValueError, 1, True],  # Fatal error case
    ],
)
def test_initialize_registry(
    monkeypatch, refresh_side_effect, num_expected_refresh_calls, expect_exit_call
):
    # This is just to make the test faster.
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    exit_mock = mock.MagicMock()
    monkeypatch.setattr(builtins, "exit", exit_mock)

    registry = DummyRegistry()
    registry.refresh.side_effect = refresh_side_effect

    registry.initialize()

    registry.refresh.assert_has_calls([mock.call()] * num_expected_refresh_calls)

    if expect_exit_call:
        exit_mock.assert_called_once()


def test_schedule__json():
    class DummyFooSchedule(server.Schedule):
        pass

    dummy_schedule = DummyFooSchedule()
    dummy_schedule._black = "beans"

    expected = {"type": "DUMMY_FOO", "parameters": {"black": "beans"}}

    assert expected == dummy_schedule.json()


def test_schedule__abstract_methods():
    schedule = server.Schedule()

    with pytest.raises(NotImplementedError):
        schedule.job_kwargs()


def test_task__json():
    class DummyBarTask(server.Task):
        pass

    task = DummyBarTask()
    task._mint = "mundo"

    expected = {"type": "DUMMY_BAR", "parameters": {"mint": "mundo"}, "schedule": None}

    assert expected == task.json()


def test_task__abstract_methods():
    task = server.Task()

    with pytest.raises(NotImplementedError):
        task.run()


def test_registry__abstract_methods():
    registry = server.Registry()

    with pytest.raises(NotImplementedError):
        registry.all_tasks()

    with pytest.raises(NotImplementedError):
        registry.refresh()


def test_transiter_registry__no_refresh():
    registry = server.TransiterRegistry()
    tasks = [mock.MagicMock(), mock.MagicMock()]
    registry._tasks = tasks

    registry.refresh()

    assert tasks == registry._tasks


def test_app_refresh_tasks(monkeypatch):
    registry = mock.MagicMock()
    metrics = mock.MagicMock()
    monkeypatch.setattr(server, "feed_auto_update_registry", registry)
    monkeypatch.setattr(server, "metrics_populator", metrics)

    server.app_refresh_tasks()

    registry.refresh.assert_called_once()
    metrics.refresh.assert_called_once()


def test_create_app(monkeypatch, scheduler):
    registry_1 = mock.MagicMock()
    monkeypatch.setattr(server, "feed_auto_update_registry", registry_1)
    registry_2 = mock.MagicMock()
    monkeypatch.setattr(server, "transiter_registry", registry_2)
    metrics = mock.MagicMock()
    monkeypatch.setattr(server, "metrics_populator", metrics)

    server.create_app()

    scheduler.start.assert_called_once()
    registry_1.initialize.assert_called_once()
    registry_2.initialize.assert_called_once()
