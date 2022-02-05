from unittest import mock

import flask
import pytest


@pytest.fixture
def flask_request(monkeypatch):
    request = mock.MagicMock(headers={}, args={})
    monkeypatch.setattr(flask, "request", request)
    return request


@pytest.fixture
def flask_url(monkeypatch):
    fake_url = "http://www.transiter.dev/entity"
    monkeypatch.setattr(flask, "url_for", lambda *args, **kwargs: fake_url)
    return fake_url
