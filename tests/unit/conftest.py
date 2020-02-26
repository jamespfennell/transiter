import contextlib
import datetime

import pytest

from transiter.data import dbconnection


@pytest.fixture
def no_op_unit_of_work(monkeypatch):
    @contextlib.contextmanager
    def no_op_context_manager():
        yield ""

    monkeypatch.setattr(dbconnection, "inline_unit_of_work", no_op_context_manager)


@pytest.fixture
def datetime_now(monkeypatch):
    """
    Mocks datetime.datetime.now() and returns the datetime object that will be returned.
    """
    now = datetime.datetime(
        year=2000, month=5, day=6, hour=7, minute=8, second=9, microsecond=10
    )

    class MockedDatetime(datetime.datetime):
        @classmethod
        def now(cls, *args, **kwargs):
            return now

    monkeypatch.setattr(datetime, "datetime", MockedDatetime)
    return now
