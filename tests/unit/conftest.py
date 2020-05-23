import contextlib
import datetime
from unittest import mock

import pytest

from transiter.db import dbconnection


@pytest.fixture(autouse=True)
def block_db_access(monkeypatch):
    def get_session(*args, **kwargs):
        raise Exception("Attempting to get a DB session in a unit test!")

    monkeypatch.setattr(dbconnection, "get_session", get_session)


class SessionFactory:
    def __init__(self):
        self.merged = []
        self.deleted = []

    def merge(self, entity):
        self.merged.append(entity)

    def delete(self, entity):
        self.deleted.append(entity)


@pytest.fixture
def session_factory():
    return SessionFactory


@pytest.fixture
def inline_unit_of_work(monkeypatch, block_db_access):

    session_started = False
    session = mock.MagicMock()

    @contextlib.contextmanager
    def inline_unit_of_work():
        nonlocal session_started
        session_started = True
        yield session

    def get_session(*args, **kwargs):
        nonlocal session_started
        if not session_started:
            raise dbconnection.OutsideUnitOfWorkError
        return session

    monkeypatch.setattr(dbconnection, "inline_unit_of_work", inline_unit_of_work)
    monkeypatch.setattr(dbconnection, "get_session", get_session)
    return session


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
