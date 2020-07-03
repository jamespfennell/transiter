"""
The HTTP Manager has primary responsibility over mapping HTTP requests to
specific Python functions (the endpoints), and converting the responses of
those functions to HTTP responses. Its methods are designed to be invoked
solely through decorators, thus completely separating business logic from
HTTP logic.

Specifically, the HTTP Manager currently does three things:
1. Uses the Flask library to correctly set up the HTTP request to Python
   function mappings.
2. Implements all of the logic for mapping Transiter service layer responses
   (which are typically Python dicts) to 3 tuples
   (string response, HTTP code, HTTP headers) that are then used by Flask to
   send the correct HTTP response.
3. Converts service layer Links to HTTP URLs. This is done with the assistance
   of the link_target decorator, which is used to identify which endpoints
   correspond to which Links.
"""
import dataclasses
import decimal
import enum
import inspect
import json
import logging
from datetime import date, datetime

import flask
from decorator import decorator

from transiter import exceptions
from transiter.services import views

logger = logging.getLogger(__name__)


class HttpStatus(enum.IntEnum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503


_exception_type_to_http_status = {
    exceptions.AccessDenied: HttpStatus.FORBIDDEN,
    exceptions.UnexpectedError: HttpStatus.INTERNAL_SERVER_ERROR,
    exceptions.IdNotFoundError: HttpStatus.NOT_FOUND,
    exceptions.PageNotFound: HttpStatus.NOT_FOUND,
    exceptions.MethodNotAllowed: HttpStatus.METHOD_NOT_ALLOWED,
    exceptions.InstallError: HttpStatus.INTERNAL_SERVER_ERROR,
    exceptions.InvalidInput: HttpStatus.BAD_REQUEST,
    exceptions.InvalidSystemConfigFile: HttpStatus.BAD_REQUEST,
    exceptions.InvalidPermissionsLevelInRequest: HttpStatus.INTERNAL_SERVER_ERROR,
    exceptions.InternalDocumentationMisconfigured: HttpStatus.SERVICE_UNAVAILABLE,
}


class HttpMethod(enum.Enum):
    DELETE = "DELETE"
    GET = "GET"
    POST = "POST"
    PUT = "PUT"


def http_endpoint(
    flask_entity,
    flask_rule,
    method: HttpMethod = HttpMethod.GET,
    returns_json_response: bool = True,
):
    """
    Decorator factory used to easily register a Transiter HTTP endpoint.

    :param flask_entity: either the Flask app or a Flask blueprint
    :param flask_rule: the URL relative to the Flask entity
    :param method: which HTTP method this endpoint uses
    :param returns_json_response: whether to format the response as JSON and apply
        appropriate HTTP headers
    """
    decorators = [
        register_documented_endpoint(flask_rule, method.value),
        flask_entity.route(flask_rule + "/", methods=[method.value]),
        flask_entity.route(flask_rule, methods=[method.value]),
    ]
    if returns_json_response:
        decorators.append(_json_response)

    def composed_decorator(func):
        for decorator_ in reversed(decorators):
            func = decorator_(func)
        return func

    return composed_decorator


@dataclasses.dataclass
class _DocumentedEndpoint:
    rule: str  # TODO; remove, unused
    method: str
    func: str

    @property
    def doc(self):
        return self.func.__doc__

    @property
    def module(self):
        return self.func.__module__


_documented_endpoints = []


def get_documented_endpoints():
    return _documented_endpoints


def register_documented_endpoint(flask_rule, method):
    def decorator_(func):
        _documented_endpoints.append(
            _DocumentedEndpoint(rule=flask_rule, method=method, func=func,)
        )
        return func

    return decorator_


@decorator
def _json_response(func, *args, **kwargs):
    response = func(*args, **kwargs)
    status = HttpStatus.OK
    if (
        isinstance(response, tuple)
        and len(response) == 2
        and isinstance(response[1], HttpStatus)
    ):
        response, status = response
    return flask.Response(
        response=_convert_to_json_str(response),
        status=status,
        content_type="application/json",
    )


_link_type_to_target = {}


@dataclasses.dataclass
class ViewTarget:
    target_str: str
    target_param_to_view_param: dict


_view_to_target = {}


def link_target(link_type, view_params=None):
    """
    This decorator factory is used to identify a HTTP endpoint with a given
    view class. It's used as follows:

    .. code-block:: python

        @link_target(views.Stop, ["id"])
        def http_endpoint_to_link(stop_id):
            pass

    :param link_type: the view type
    :param view_params: a list of string field names in the view whose values would be
     passed to the endpoint to get the response for that view object.
    :return: the factory returns a decorator to be applied to the endpoint.
    """

    def views_decorator(func):
        flask_endpoint = "{}.{}".format(func.__module__, func.__name__)
        target_param_to_view_param = {}
        if view_params is not None:
            for i, target_param in enumerate(inspect.signature(func).parameters.keys()):
                target_param_to_view_param[target_param] = view_params[i]
        _view_to_target[link_type] = ViewTarget(
            flask_endpoint, target_param_to_view_param
        )
        return func

    return views_decorator


def get_url_parameters(expected_keys, error_if_extra_keys=True):
    all_request_args = flask.request.args
    if error_if_extra_keys:
        extra_keys = set(all_request_args.keys()) - set(expected_keys)
        if len(extra_keys) > 0:
            raise exceptions.InvalidInput(
                "Unknown URL parameters: {}. Valid URL parameters for this endpoint: {}".format(
                    extra_keys, expected_keys
                )
            )
    return {key: all_request_args.get(key) for key in expected_keys}


def is_sync_request():
    return (
        get_url_parameters(["sync"], error_if_extra_keys=False).get("sync", "false")
        == "true"
    )


def get_float_url_parameter(key, default=None, required=False):
    raw_value = flask.request.args.get(key)
    if raw_value is None:
        if not required:
            return default
        raise exceptions.InvalidInput(f"The URL parameter '{key}' is required.")
    try:
        return float(raw_value)
    except ValueError:
        raise exceptions.InvalidInput(
            f"Received non-float value '{raw_value}' for float URL parameter '{key}'."
        )


def get_list_url_parameter(key, required=False):
    raw = flask.request.args.getlist(key)
    if len(raw) == 0:
        if not required:
            return None
        raise exceptions.InvalidInput(f"The URL parameter '{key}' is required.")
    return raw


def get_enum_url_parameter(key, enum_, default=None):
    raw_value = flask.request.args.get(key)
    if raw_value is None:
        return default
    try:
        return enum_[raw_value.upper()]
    except KeyError:
        raise exceptions.InvalidInput(
            (
                "Received unexpected value '{}' for URL parameter '{}'. "
                "Valid values are {} (case insensitive)."
            ).format(
                raw_value,
                key,
                ", ".join(["'{}'".format(element.name) for element in enum_]),
            )
        )


def convert_exception_to_error_response(exception):
    # noinspection PyBroadException
    try:
        logger.debug("Exception", exc_info=True)
        return flask.Response(
            response=_convert_to_json_str(exception.response()),
            status=_exception_type_to_http_status[type(exception)],
            content_type="application/json",
        )
    except Exception:
        logger.exception("Unexpected exception in processing HTTP request.")
        return flask.Response(response="", status=HttpStatus.INTERNAL_SERVER_ERROR)


def _convert_to_json_str(data):
    """
    Convert a server layer response to a JSON string.
    """
    return json.dumps(
        data, indent=2, separators=(",", ": "), default=_transiter_json_serializer
    )


def _build_href(view: views.View):
    if type(view) not in _view_to_target:
        return None
    view_target = _view_to_target[type(view)]
    custom_host = flask.request.headers.get("X-Transiter-Host")
    kwargs = {
        key: getattr(view, value)
        for key, value in view_target.target_param_to_view_param.items()
    }
    if custom_host is not None:
        return custom_host + flask.url_for(
            view_target.target_str, _external=False, **kwargs
        )
    return flask.url_for(view_target.target_str, _external=True, **kwargs)


def _transiter_json_serializer(obj):
    """
    This is custom Transiter JSON serializer for objects that are not
    serializable by default.
    """
    if isinstance(obj, views.View):
        base = obj.to_dict()
        href = _build_href(obj)
        if href is not None:
            base["href"] = href
        return base

    if isinstance(obj, (datetime, date)):
        return obj.timestamp()

    if isinstance(obj, enum.Enum):
        return obj.name

    if isinstance(obj, decimal.Decimal):
        return str(obj)

    raise TypeError("Type {} not serializable".format(type(obj)))
