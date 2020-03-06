import pytest

from transiter.scheduler import server
from transiter.services import feedservice


class DummyJob:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def reschedule(self, *args, **kwargs):
        self.scheduler.num_updated_jobs += 1

    def modify(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        self.scheduler.remove_job()


class DummyScheduler:
    def __init__(self):
        self.num_added_jobs = 0
        self.num_updated_jobs = 0
        self.num_deleted_jobs = 0

    def add_job(self, *args, **kwargs):
        self.num_added_jobs += 1
        return DummyJob(self)

    def remove_job(self):
        self.num_deleted_jobs += 1


@pytest.fixture
def dummy_scheduler(monkeypatch):
    scheduler = DummyScheduler()
    monkeypatch.setattr(server, "scheduler", scheduler)
    return scheduler


def test_add_new_feed_update(monkeypatch, dummy_scheduler):
    server.feed_pk_to_auto_update_task = {}
    monkeypatch.setattr(
        feedservice,
        "list_all_auto_updating",
        lambda: [{"auto_update_period": 5, "id": "A", "system_id": "B", "pk": 3}],
    )

    server.refresh_feed_auto_update_tasks()

    assert len(server.feed_pk_to_auto_update_task) == 1
    assert dummy_scheduler.num_added_jobs == 1
    assert dummy_scheduler.num_updated_jobs == 0


def test_update_feed_update(monkeypatch, dummy_scheduler):
    server.feed_pk_to_auto_update_task = {3: server.FeedAutoUpdateTask("A", "B", 3)}
    monkeypatch.setattr(
        feedservice,
        "list_all_auto_updating",
        lambda: [{"auto_update_period": 5, "id": "A", "system_id": "B", "pk": 3}],
    )
    server.refresh_feed_auto_update_tasks()

    assert len(server.feed_pk_to_auto_update_task) == 1
    assert dummy_scheduler.num_added_jobs == 1
    assert dummy_scheduler.num_updated_jobs == 1


def test_stop_feed_update(monkeypatch, dummy_scheduler):
    server.feed_pk_to_auto_update_task = {3: DummyJob(dummy_scheduler)}
    monkeypatch.setattr(
        feedservice, "list_all_auto_updating", lambda: [],
    )

    server.refresh_feed_auto_update_tasks()

    assert len(server.feed_pk_to_auto_update_task) == 0
    assert dummy_scheduler.num_added_jobs == 0
    assert dummy_scheduler.num_updated_jobs == 0
    assert dummy_scheduler.num_deleted_jobs == 1
