import dataclasses
import datetime
import decimal
import enum

import flask
import pytest

from transiter import exceptions
from transiter.http import httpmanager
from transiter.services import views


# NOTE: Most of the test coverage of the HTTP manager comes from the endpoint
# testing in which the HTTP manager is not mocked. This testing class is
# designed to capture a few of the cases no captured in the endpoint testing.


def test_unexpected_error():
    """[HTTP Manager] Unexpected error"""

    response = httpmanager.convert_exception_to_error_response(ValueError())

    assert httpmanager.HttpStatus.INTERNAL_SERVER_ERROR == response.status_code


def test_all_exceptions_inherit_from_transiter_exceptions():
    """[HTTP Manager] Ensure every exception inherits from TransiterException"""
    for exception_variable in exceptions.__dict__.values():
        try:
            if not issubclass(exception_variable, Exception):
                continue
        except TypeError:
            # NOTE: this happens if exception_variable is not a class.
            continue
        assert issubclass(exception_variable, exceptions.TransiterException)


def test_all_exceptions_have_http_status():
    """[HTTP Manager] Ensure every exception has a HTTP status"""
    for transiter_exception in exceptions.TransiterException.__subclasses__():
        assert transiter_exception in httpmanager._exception_type_to_http_status


def test_get_request_args__extra_keys(flask_request):
    """[HTTP Manager] Extra GET parameters"""
    flask_request.args = {"key_1": "value_1", "key_2": "value_2"}

    with pytest.raises(exceptions.InvalidInput):
        httpmanager.get_url_parameters(["key_1"])


def test_build_href(flask_url, flask_request):
    class FakeLink(views.View):
        pass

    @httpmanager.link_target(FakeLink)
    def entity():
        pass

    flask_request.headers = {}

    assert flask_url == httpmanager._build_href(FakeLink())


def test_build_href__links_with_host(flask_url, flask_request):
    class FakeLink(views.View):
        pass

    @httpmanager.link_target(FakeLink)
    def entity():
        pass

    custom_host = "my_host"
    flask_request.headers = {"X-Transiter-Host": custom_host}

    assert custom_host + flask_url == httpmanager._build_href(FakeLink())


def test_json_serialization__views(flask_url, flask_request):
    @dataclasses.dataclass
    class MyView(views.View):
        id: str
        _system_id: str

    expected = {"id": "my_id"}

    actual = httpmanager._transiter_json_serializer(
        MyView(id="my_id", _system_id="system_id")
    )

    assert actual == expected


def test_json_serialization__datetime():
    """[HTTP Manager] JSON serialization of datetimes"""
    timestamp = 24536456

    dt = datetime.datetime.fromtimestamp(timestamp)

    assert timestamp == httpmanager._transiter_json_serializer(dt)


def test_json_serialization__enum():
    """[HTTP Manager] JSON serialization of enums"""

    class MyEnum(enum.Enum):
        FIRST = 1
        SECOND = 2

    assert "FIRST" == httpmanager._transiter_json_serializer(MyEnum.FIRST)


def test_json_serialization__decimal():
    """[HTTP Manager] JSON serialization of decimals"""

    d = decimal.Decimal("0.54")

    assert "0.54" == httpmanager._transiter_json_serializer(d)


def test_json_serialization__unknown_object():
    """[HTTP Manager] JSON serialization failure given unknown object"""

    with pytest.raises(TypeError):
        httpmanager._transiter_json_serializer(flask.Response())


@pytest.mark.parametrize("value", ["value_a", "VALUE_A", "VaLuE_a"])
def test_get_enum_url_parameter__base_case(flask_request, value):
    class TestEnum(enum.Enum):
        VALUE_A = 0
        VALUE_B = 1

    flask_request.args = {"my_param": "value_a"}

    assert TestEnum.VALUE_A == httpmanager.get_enum_url_parameter("my_param", TestEnum)


def test_get_enum_url_parameter__default_case(flask_request):
    class TestEnum(enum.Enum):
        VALUE_A = 0
        VALUE_B = 1

    flask_request.args = {}

    assert TestEnum.VALUE_A == httpmanager.get_enum_url_parameter(
        "my_param", TestEnum, TestEnum.VALUE_A
    )


def test_get_enum_url_parameter__invalid(flask_request):
    class TestEnum(enum.Enum):
        VALUE_A = 0
        VALUE_B = 1

    flask_request.args = {"my_param": "value_c"}

    with pytest.raises(exceptions.InvalidInput):
        httpmanager.get_enum_url_parameter("my_param", TestEnum)
