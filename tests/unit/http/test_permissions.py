from unittest import mock

import flask
import pytest

from transiter import exceptions
from transiter.http import permissions


@pytest.fixture
def flask_headers(monkeypatch):
    request = mock.MagicMock()
    monkeypatch.setattr(flask, "request", request)
    return request.headers


def test_invalid_request_permissions_level(flask_headers):
    flask_headers.get.return_value = "GarbageStatus"

    with pytest.raises(exceptions.InvalidPermissionsLevelInRequest):
        permissions.ensure(permissions.PermissionsLevel.ALL)


def test_no_permission(flask_headers):
    flask_headers.get.return_value = permissions.PermissionsLevel.ADMIN_READ.name

    with pytest.raises(exceptions.AccessDenied):
        permissions.ensure(permissions.PermissionsLevel.ALL)


def test_has_permission(flask_headers):
    flask_headers.get.return_value = permissions.PermissionsLevel.ALL.name

    permissions.ensure(permissions.PermissionsLevel.ADMIN_READ)
