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
import decimal
import enum
import json
import logging
from datetime import date, datetime

import flask
from decorator import decorator

from transiter import exceptions
from transiter.services import links

logger = logging.getLogger(__name__)


class HttpStatus(enum.IntEnum):
    OK = 200
    CREATED = 201
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
    exceptions.IdNotFoundError: HttpStatus.NOT_FOUND,
    exceptions.PageNotFound: HttpStatus.NOT_FOUND,
    exceptions.MethodNotAllowed: HttpStatus.METHOD_NOT_ALLOWED,
    exceptions.InstallError: HttpStatus.INTERNAL_SERVER_ERROR,
    exceptions.InvalidInput: HttpStatus.BAD_REQUEST,
    exceptions.InvalidSystemConfigFile: HttpStatus.BAD_REQUEST,
    exceptions.ConfigFileNotFoundError: HttpStatus.INTERNAL_SERVER_ERROR,
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
    status_on_success: HttpStatus = HttpStatus.OK,
):
    """
    Decorator factory used to easily register a Transiter HTTP endpoint.

    :param flask_entity: either the Flask app or a Flask blueprint
    :param flask_rule: the URL relative to the Flask entity
    :param method: which HTTP method this endpoint uses
    :param returns_json_response: whether to format the response as JSON and apply
        appropriate HTTP headers
    :param status_on_success: the HTTP status to return on success
    """
    decorators = [
        flask_entity.route(flask_rule + "/", methods=[method.value]),
        flask_entity.route(flask_rule, methods=[method.value]),
    ]
    if returns_json_response:
        decorators.append(json_response(status_on_success))

    def composed_decorator(func):
        for decorator_ in reversed(decorators):
            func = decorator_(func)
        return func

    return composed_decorator


def json_response(http_status: HttpStatus = HttpStatus.OK):
    @decorator
    def decorator_(func, *args, **kwargs):
        return flask.Response(
            response=_convert_to_json_str(func(*args, **kwargs)),
            status=http_status,
            content_type="application/json",
        )

    return decorator_


_link_type_to_target = {}


def link_target(link_type):
    """
    This decorator factory is used to identify a HTTP endpoint with a given
    link. It's used as follows:

    .. code-block:: python

        @link_target(links.RelevantLink)
        def http_endpoint_to_link():
            pass

    :param link_type: the link type
    :return: the factory returns a decorator to be applied to the endpoint.
    """

    def decorator_(func):
        flask_endpoint = "{}.{}".format(func.__module__, func.__name__)
        _link_type_to_target[link_type] = flask_endpoint
        return func

    return decorator_


def get_request_args(keys):
    all_request_args = flask.request.args
    extra_keys = set(all_request_args.keys()) - set(keys)
    if len(extra_keys) > 0:
        raise exceptions.InvalidInput(
            "Unknown GET parameters: {}. Valid parameters: {}".format(extra_keys, keys)
        )

    return {key: all_request_args.get(key) for key in keys}


def convert_exception_to_error_response(exception):
    # noinspection PyBroadException
    try:
        logger.debug("Exception", exc_info=True)
        return flask.Response(
            response=_convert_to_json_str(exception.response()),
            status=_exception_type_to_http_status[type(exception)],
            content_type="application/json",
        )
    except:
        logger.exception("Unexpected exception in processing HTTP request.")
        return flask.Response(response="", status=HttpStatus.INTERNAL_SERVER_ERROR)


def _convert_to_json_str(data):
    """
    Convert a server layer response to a JSON string.
    """
    return json.dumps(
        data, indent=2, separators=(",", ": "), default=_transiter_json_serializer
    )


def _transiter_json_serializer(obj):
    """
    This is custom Transiter JSON serializer for objects that are not
    serializable by default.
    """
    if isinstance(obj, (datetime, date)):
        return obj.timestamp()

    if isinstance(obj, enum.Enum):
        return obj.name

    if isinstance(obj, links.Link):
        target = _link_type_to_target[type(obj)]
        custom_host = flask.request.headers.get("X-Transiter-Host")
        if custom_host is not None:
            return custom_host + flask.url_for(target, _external=False, **obj.kwargs)
        return flask.url_for(target, _external=True, **obj.kwargs)

    if isinstance(obj, decimal.Decimal):
        return str(obj)

    raise TypeError("Type {} not serializable".format(type(obj)))
