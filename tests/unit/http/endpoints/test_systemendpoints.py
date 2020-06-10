from unittest import mock

import pytest
import requests
from werkzeug.datastructures import ImmutableMultiDict

from transiter import exceptions
from transiter.http import httpmanager
from transiter.http.endpoints import systemendpoints
from transiter.http.httpmanager import HttpStatus
from transiter.services import systemservice, views


@pytest.fixture
def install_service_function(monkeypatch):
    function = mock.MagicMock()
    function.return_value = True
    monkeypatch.setattr(systemservice, "install", function)
    return function


@pytest.fixture
def get_service_function(monkeypatch):
    function = mock.MagicMock()
    function.return_value = {}
    monkeypatch.setattr(systemservice, "get_by_id", function)
    return function


@pytest.fixture
def get_update_function(monkeypatch):
    function = mock.MagicMock()
    function.return_value = {}
    monkeypatch.setattr(systemservice, "get_update_by_id", function)
    return function


@pytest.fixture
def get_request_args(monkeypatch):
    function = mock.MagicMock()
    function.return_value = {}
    monkeypatch.setattr(httpmanager, "get_url_parameters", function)
    return function


@pytest.mark.parametrize("extra_params", [{}, {"key_1": "value_1"}])
@pytest.mark.parametrize(
    "sync,update_status,expected_http_status",
    [
        (True, views.SystemUpdateStatus.SUCCESS, HttpStatus.CREATED),
        (True, views.SystemUpdateStatus.FAILED, HttpStatus.BAD_REQUEST),
        (False, views.SystemUpdateStatus.SCHEDULED, HttpStatus.ACCEPTED),
    ],
)
def test_install__config_file_from_url(
    monkeypatch,
    flask_request,
    install_service_function,
    get_update_function,
    get_request_args,
    sync,
    update_status,
    expected_http_status,
    extra_params,
):
    if extra_params is None:
        extra_params = {}
    get_update_function.return_value = views.SystemUpdate(
        status=update_status, id="", scheduled_at=0, completed_at=0, stack_trace=[]
    )
    install_method = install_service_function

    get_request_args.return_value = {"sync": str(sync).lower()}
    flask_request.form = ImmutableMultiDict(
        [("config_file", "config_file_url")] + list(extra_params.items())
    )
    flask_request.files = ImmutableMultiDict()

    requests_response = mock.MagicMock()
    requests_response.text = "config_string"
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: requests_response)

    response = systemendpoints.install("system_id")

    assert expected_http_status == response.status_code

    install_method.assert_called_once_with(
        system_id="system_id",
        config_str="config_string",
        extra_settings=extra_params,
        config_source_url="config_file_url",
        sync=sync,
    )


def test_install__config_file_from_url__failed_to_download(
    monkeypatch,
    flask_request,
    install_service_function,
    get_update_function,
    get_request_args,
):
    get_request_args.return_value = {"sync": None}
    flask_request.form = ImmutableMultiDict([("config_file", "config_file_url")])
    flask_request.files = ImmutableMultiDict()

    install_service_function.return_value = True

    requests_response = mock.MagicMock()
    requests_response.raise_for_status.side_effect = (
        requests.exceptions.RequestException()
    )
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: requests_response)

    with pytest.raises(exceptions.InvalidInput):
        systemendpoints.install("system_id")

    install_service_function.assert_not_called()


@pytest.mark.parametrize(
    "extra_params", [pytest.param({}), pytest.param({"key_1": "value_1"})]
)
@pytest.mark.parametrize(
    "sync,update_status,expected_http_status",
    [
        (True, views.SystemUpdateStatus.SUCCESS, HttpStatus.CREATED),
        (True, views.SystemUpdateStatus.FAILED, HttpStatus.BAD_REQUEST),
        (False, views.SystemUpdateStatus.SCHEDULED, HttpStatus.ACCEPTED),
    ],
)
def test_install__config_file_from_file_upload(
    flask_request,
    install_service_function,
    get_update_function,
    get_request_args,
    sync,
    update_status,
    expected_http_status,
    extra_params,
):
    get_update_function.return_value = views.SystemUpdate(
        status=update_status, id="", scheduled_at=0, completed_at=0, stack_trace=[]
    )
    install_method = install_service_function

    flask_request.form = ImmutableMultiDict(list(extra_params.items()))
    get_request_args.return_value = {"sync": str(sync).lower()}

    file_contents = "config_string"
    file_upload_object = mock.MagicMock()
    file_upload_object.read.return_value = file_contents.encode("utf-8")
    flask_request.files = ImmutableMultiDict([("config_file", file_upload_object)])

    response = systemendpoints.install("system_id")

    assert expected_http_status == response.status_code
    install_method.assert_called_once_with(
        system_id="system_id",
        config_str=file_contents,
        extra_settings=extra_params,
        config_source_url=None,
        sync=sync,
    )


def test_install__no_config_file(
    flask_request, get_request_args, install_service_function
):
    get_request_args.return_value = {"sync": None}
    flask_request.form = ImmutableMultiDict()
    flask_request.files = ImmutableMultiDict()

    with pytest.raises(exceptions.InvalidInput):
        systemendpoints.install("system_id")

    install_service_function.assert_not_called()
