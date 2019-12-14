import pytest
import datetime


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
