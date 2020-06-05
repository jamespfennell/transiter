import json
from unittest import mock

import flask
import pytest
from werkzeug import datastructures

from transiter import config, exceptions
from transiter.http import flaskapp, permissions
from transiter.http.endpoints import (
    agencyendpoints,
    feedendpoints,
    routeendpoints,
    stopendpoints,
    systemendpoints,
    tripendpoints,
)
from transiter.http.httpmanager import HttpStatus
from transiter.services import (
    agencyservice,
    feedservice,
    routeservice,
    stopservice,
    systemservice,
    tripservice,
)


# NOTE: there are mostly two orthogonal things being tested here:
#
# 1. That the HTTP manager works correctly in enforcing permissions and converting
#    service layer responses to HTTP responses.
#
# 2. Given a certain endpoint, the right service layer function is called.
#
# Number 2 is of dubious value. If it becomes hard to maintain, we can stop testing
# that.


@pytest.mark.parametrize(
    "request_permissions_level",
    [
        pytest.param(permissions.PermissionsLevel.USER_READ),
        pytest.param(permissions.PermissionsLevel.ADMIN_READ),
    ],
)
@pytest.mark.parametrize(
    "endpoint_function,function_args",
    [
        pytest.param(systemendpoints.install, ["system_id"]),
        pytest.param(systemendpoints.delete_by_id, ["system_id"]),
        pytest.param(feedendpoints.create_feed_update, ["system_id", "feed_id"]),
        pytest.param(feedendpoints.create_feed_update_flush, ["system_id", "feed_id"]),
    ],
)
def test_permission_denied__admin_write_endpoints(
    flask_request, endpoint_function, function_args, request_permissions_level
):
    """[Endpoints] Permission denied, admin write."""
    flask_request.headers = {
        "X-Transiter-PermissionsLevel": request_permissions_level.name
    }

    with pytest.raises(exceptions.AccessDenied):
        endpoint_function(*function_args)


@pytest.mark.parametrize(
    "endpoint_function,function_args",
    [
        pytest.param(feedendpoints.list_all_in_system, ["system_id"]),
        pytest.param(feedendpoints.get_in_system_by_id, ["system_id", "feed_id"]),
        pytest.param(feedendpoints.list_updates_in_feed, ["system_id", "feed_id"]),
    ],
)
def test_permission_denied__admin_read_endpoints(
    flask_request, endpoint_function, function_args
):
    """[Endpoints] Permission denied, admin read."""
    flask_request.headers = {
        "X-Transiter-PermissionsLevel": permissions.PermissionsLevel.USER_READ.name
    }

    with pytest.raises(exceptions.AccessDenied):
        endpoint_function(*function_args)


@pytest.mark.parametrize(
    "endpoints_module,service_module,function_name,function_args,function_kwargs",
    [
        pytest.param(systemendpoints, systemservice, "list_all", [], {}),
        pytest.param(systemendpoints, systemservice, "get_by_id", ["system_id"], {}),
        pytest.param(
            routeendpoints,
            routeservice,
            "list_all_in_system",
            ["system_id"],
            {"alerts_detail": None},
        ),
        pytest.param(
            routeendpoints,
            routeservice,
            "get_in_system_by_id",
            ["system_id", "route_id"],
            {"alerts_detail": None},
        ),
        pytest.param(
            feedendpoints, feedservice, "list_all_in_system", ["system_id"], {}
        ),
        pytest.param(
            feedendpoints,
            feedservice,
            "get_in_system_by_id",
            ["system_id", "feed_id"],
            {},
        ),
        pytest.param(
            feedendpoints,
            feedservice,
            "list_updates_in_feed",
            ["system_id", "feed_id"],
            {},
        ),
        pytest.param(
            stopendpoints,
            stopservice,
            "list_all_in_system",
            ["system_id"],
            {"alerts_detail": None},
        ),
        pytest.param(
            tripendpoints,
            tripservice,
            "list_all_in_route",
            ["system_id", "route_id"],
            {"alerts_detail": None},
        ),
        pytest.param(
            tripendpoints,
            tripservice,
            "get_in_route_by_id",
            ["system_id", "route_id", "trip_id"],
            {"alerts_detail": None},
        ),
        [
            agencyendpoints,
            agencyservice,
            "list_all_in_system",
            ["system_id"],
            {"alerts_detail": None},
        ],
        [
            agencyendpoints,
            agencyservice,
            "get_in_system_by_id",
            ["system_id", "agency_id"],
            {"alerts_detail": None},
        ],
    ],
)
def test_simple_endpoints(
    monkeypatch,
    endpoints_module,
    service_module,
    function_name,
    function_args,
    function_kwargs,
):
    endpoints_test_helper(
        monkeypatch,
        endpoints_module,
        service_module,
        function_name,
        function_args,
        function_kwargs,
    )


def test_stop_endpoints__get_in_system_by_id(monkeypatch):
    endpoints_test_helper(
        monkeypatch,
        stopendpoints,
        stopservice,
        "get_in_system_by_id",
        ["system_id", "stop_id"],
        {
            "alerts_detail": None,
            "minimum_number_of_trips": None,
            "include_all_trips_within": None,
            "exclude_trips_before": None,
        },
    )


def test_system_endpoints__list_all_transfers(monkeypatch):
    endpoints_test_helper(
        monkeypatch,
        systemendpoints,
        stopservice,
        "list_all_transfers_in_system",
        ["system_id"],
        {"from_stop_ids": None, "to_stop_ids": None},
    )


def test_system_endpoints__delete_by_id(monkeypatch):
    endpoints_test_helper(
        monkeypatch,
        systemendpoints,
        systemservice,
        "delete_by_id",
        ["system_id"],
        function_kwargs={"error_if_not_exists": True, "sync": False},
        expected_http_status=HttpStatus.NO_CONTENT,
        expected_content="",
        expected_content_type="",
    )


def endpoints_test_helper(
    monkeypatch,
    endpoints_module,
    service_module,
    function_name,
    function_args,
    function_kwargs=None,
    expected_http_status=HttpStatus.OK,
    expected_content=None,
    expected_content_type="application/json",
):
    if function_kwargs is None:
        function_kwargs = {}

    monkeypatch.setattr(
        flask, "request", mock.MagicMock(headers={}, args=datastructures.MultiDict())
    )

    service_layer_response = "TEST"
    service_layer_function = mock.MagicMock()
    service_layer_function.return_value = service_layer_response
    monkeypatch.setattr(service_module, function_name, service_layer_function)

    if expected_content is None:
        expected_content = json.dumps(service_layer_response)

    response = getattr(endpoints_module, function_name)(*function_args)

    assert expected_content == response.get_data(as_text=True)
    assert expected_http_status == response.status_code
    assert expected_content_type == response.content_type
    service_layer_function.assert_called_once_with(*function_args, **function_kwargs)


@pytest.mark.parametrize(
    "internal_documentation_enabled", [pytest.param(True), pytest.param(False)],
)
def test_flask_app_root(
    monkeypatch, flask_request, flask_url, internal_documentation_enabled
):
    """[Endpoints] flask app root"""
    num_systems = 2
    monkeypatch.setattr(systemservice, "list_all", lambda: [None] * num_systems)
    monkeypatch.setattr(config, "DOCUMENTATION_ENABLED", internal_documentation_enabled)

    response = flaskapp.root()

    json_response = json.loads(response.get_data(as_text=True))

    assert num_systems == json_response["systems"]["count"]
    assert HttpStatus.OK == response.status_code


def test_404(flask_request):
    """[Flask app] Test 404 error"""
    flask_request.path = "/missing/path"

    response = flaskapp.page_not_found(None)

    assert HttpStatus.NOT_FOUND == response.status_code


def test_launch(monkeypatch):
    app = mock.MagicMock()
    monkeypatch.setattr(flaskapp, "app", app)

    flaskapp.launch()

    app.run.assert_called_once_with(port=8000, debug=True)
