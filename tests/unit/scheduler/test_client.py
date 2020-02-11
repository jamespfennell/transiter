import unittest.mock as mock

import requests
import pytest
from transiter.scheduler import client


@pytest.fixture
def scheduler_response(monkeypatch):
    response = mock.Mock()

    def post(*args, **kwargs):
        return response

    monkeypatch.setattr(requests, "post", post)
    return response


def test_refresh_tasks__pass(scheduler_response):
    scheduler_response.raise_for_status = lambda: None

    assert client.refresh_tasks() is True


def test_refresh_tasks__fail(scheduler_response):
    scheduler_response.raise_for_status.side_effect = requests.RequestException()

    assert client.refresh_tasks() is False


def test_refresh_tasks__do_not_swallow_all_exceptions(scheduler_response):
    scheduler_response.raise_for_status.side_effect = ValueError()

    with pytest.raises(ValueError):
        client.refresh_tasks()
