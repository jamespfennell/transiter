import unittest.mock as mock

import pytest
import requests

from transiter.scheduler import client


@pytest.fixture
def scheduler_post_response(monkeypatch):
    response = mock.Mock()

    def post(*args, **kwargs):
        return response

    monkeypatch.setattr(requests, "post", post)
    return response


@pytest.fixture
def scheduler_get_response(monkeypatch):
    response = mock.Mock()

    def get(*args, **kwargs):
        return response

    monkeypatch.setattr(requests, "get", get)
    return response


def test_ping__pass(scheduler_get_response):
    scheduler_get_response.raise_for_status = lambda: None
    scheduler_get_response.text = "3"

    assert client.ping() == 3


def test_ping__fail(scheduler_get_response):
    scheduler_get_response.raise_for_status.side_effect = requests.RequestException()

    assert client.ping() is None


def test_refresh_tasks__pass(scheduler_post_response):
    scheduler_post_response.raise_for_status = lambda: None

    assert client.refresh_tasks() is True


def test_refresh_tasks__fail(scheduler_post_response):
    scheduler_post_response.raise_for_status.side_effect = requests.RequestException()

    assert client.refresh_tasks() is False


def test_refresh_tasks__do_not_swallow_all_exceptions(scheduler_post_response):
    scheduler_post_response.raise_for_status.side_effect = ValueError()

    with pytest.raises(ValueError):
        client.refresh_tasks()
