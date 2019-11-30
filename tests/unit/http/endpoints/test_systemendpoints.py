from unittest import mock

import requests
from werkzeug.datastructures import ImmutableMultiDict

from transiter.http.endpoints import systemendpoints
from transiter.http.httpmanager import HttpStatus
from transiter.services import systemservice
import pytest


@pytest.fixture
def install_service_function(monkeypatch):
    function = mock.MagicMock()
    function.return_value = True
    monkeypatch.setattr(systemservice, "install", function)
    return function


@pytest.mark.parametrize(
    "extra_params", [pytest.param({}), pytest.param({"key_1": "value_1"})]
)
@pytest.mark.parametrize(
    "service_layer_response,expected_http_status",
    [
        pytest.param(True, HttpStatus.CREATED),
        pytest.param(False, HttpStatus.NO_CONTENT),
    ],
)
def test_install__config_file_from_url(
    monkeypatch,
    flask_request,
    install_service_function,
    service_layer_response,
    expected_http_status,
    extra_params,
):
    if extra_params is None:
        extra_params = {}

    flask_request.form = ImmutableMultiDict(
        [("config_file", "config_file_url")] + list(extra_params.items())
    )
    flask_request.files = ImmutableMultiDict()

    install_service_function.return_value = service_layer_response

    requests_response = mock.MagicMock()
    requests_response.text = "config_string"
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: requests_response)

    response = systemendpoints.install("system_id")

    assert expected_http_status == response.status_code
    install_service_function.assert_called_once_with(
        system_id="system_id", config_str="config_string", extra_settings=extra_params
    )


def test_install__config_file_from_url__failed_to_download(
    monkeypatch, flask_request, install_service_function
):
    flask_request.form = ImmutableMultiDict([("config_file", "config_file_url")])
    flask_request.files = ImmutableMultiDict()

    install_service_function.return_value = True

    requests_response = mock.MagicMock()
    requests_response.raise_for_status.side_effect = (
        requests.exceptions.RequestException()
    )
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: requests_response)

    response = systemendpoints.install("system_id")

    assert HttpStatus.BAD_REQUEST == response.status_code
    install_service_function.assert_not_called()


@pytest.mark.parametrize(
    "extra_params", [pytest.param({}), pytest.param({"key_1": "value_1"})]
)
@pytest.mark.parametrize(
    "service_layer_response,expected_http_status",
    [
        pytest.param(True, HttpStatus.CREATED),
        pytest.param(False, HttpStatus.NO_CONTENT),
    ],
)
def test_install__config_file_from_file_upload(
    flask_request,
    install_service_function,
    service_layer_response,
    expected_http_status,
    extra_params,
):
    flask_request.form = ImmutableMultiDict(list(extra_params.items()))

    file_contents = "config_string"
    file_upload_object = mock.MagicMock()
    file_upload_object.read.return_value = file_contents.encode("utf-8")
    flask_request.files = ImmutableMultiDict([("config_file", file_upload_object)])

    install_service_function.return_value = service_layer_response

    response = systemendpoints.install("system_id")

    assert expected_http_status == response.status_code
    install_service_function.assert_called_once_with(
        system_id="system_id", config_str=file_contents, extra_settings=extra_params
    )


def test_install__no_config_file(flask_request, install_service_function):
    flask_request.form = ImmutableMultiDict()
    flask_request.files = ImmutableMultiDict()

    response = systemendpoints.install("system_id")

    assert HttpStatus.BAD_REQUEST == response.status_code
    install_service_function.assert_not_called()
