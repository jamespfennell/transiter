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
import enum
import json
import logging
from datetime import date, datetime

import flask
from decorator import decorator

from transiter import exceptions
from transiter.services import links

logger = logging.getLogger(__name__)


class HttpHeader(enum.Enum):
    CONTENT_TYPE_JSON = {"Content-Type": "application/json"}


class HttpStatus(enum.IntEnum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501


_exception_type_to_http_status = {
    exceptions.AccessDenied: HttpStatus.FORBIDDEN,
    exceptions.IdNotFoundError: HttpStatus.NOT_FOUND,
    exceptions.InstallError: HttpStatus.INTERNAL_SERVER_ERROR,
    exceptions.InvalidInput: HttpStatus.BAD_REQUEST,
    exceptions.InvalidSystemConfigFile: HttpStatus.BAD_REQUEST,
    exceptions.ConfigFileNotFoundError: HttpStatus.INTERNAL_SERVER_ERROR,
    exceptions.InvalidPermissionsLevelInRequest: HttpStatus.INTERNAL_SERVER_ERROR,
}


class HttpMethod(enum.Enum):
    DELETE = "DELETE"
    GET = "GET"
    POST = "POST"
    PUT = "PUT"


class RequestType(enum.Enum):
    """
    The request type simultaneously determines which HTTP method the function
    being decorated should respond to, and how Transiter should convert the
    service layer response to a HTTP response. The value of the enum is the
    relevant HttpMethod.
    """

    CREATE = HttpMethod.PUT
    DELETE = HttpMethod.DELETE
    GET = HttpMethod.GET
    UPDATE = HttpMethod.POST


def http_endpoint(flask_entity, flask_rule, request_type=RequestType.GET):
    """
    Decorator factory used to register a Transiter HTTP endpoint.

    This decorator factory simply composes the relevant Flask decorator, for the
    HTTP routing, and the Transiter http_response decorator, for converting
    service layer responses into HTTP responses.

    :param flask_entity: either the Flask app or a Flask blueprint
    :param flask_rule: the URL relative to the Flask entity
    :param request_type: the endpoint type
    :return: the composed decorator
    """
    http_method = request_type.value
    flask_decorator = flask_entity.route(flask_rule, methods=[http_method.value])
    custom_decorator = http_response(request_type)

    def composed_decorator(func):
        return flask_decorator(custom_decorator(func))

    return composed_decorator


def http_response(request_type=RequestType.GET):
    """
    Decorator factory used to create decorators that convert service layer
    responses into HTTP responses.

    :param request_type: the request type
    """

    @decorator
    def decorator_(func, *args, **kwargs):
        return _perform_request(request_type, func, *args, **kwargs)

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
    all_request_args = _get_all_request_args()
    extra_keys = set(all_request_args.keys()) - set(keys)
    if len(extra_keys) > 0:
        raise exceptions.InvalidInput(
            "Unknown GET parameters: {}. Valid parameters: {}".format(extra_keys, keys)
        )

    return {key: all_request_args.get(key) for key in keys}


def _get_all_request_args():
    return flask.request.args


def _perform_request(request_type, func, *args, **kwargs):
    """
    Perform the request.

    This method is responsible for executing the function (usually just calling
    a service layer function), and converting the response to a HTTP response.
    This means converting the result to JSON, and returning relevant HTTP
    status codes and headers - these tasks are actually delegated to a post
    processor depending on the request type. The method also handles Exceptions
    that are raised.

    :param request_type: the request type
    :param func: the function that was decorated with http_endpoint
    :param args: args
    :param kwargs: kwargs
    :return: a three tuple for consumption by Flask: (response content,
        response code, and response headers)
    """
    # NOTE: the nested try blocks are to ensure that any errors encountered
    # in handling Transiter exceptions are also handled gracefully in the HTTP
    # sense.
    try:
        try:
            response = func(*args, **kwargs)
            return _request_type_to_post_processor[request_type](response)
        except exceptions._TransiterException as e:
            return (
                _convert_to_json_str(e.response()),
                _exception_type_to_http_status[type(e)],
                {**HttpHeader.CONTENT_TYPE_JSON.value},
            )
    except Exception:
        logger.exception("Unexpected exception in processing HTTP request.")
        return ("", HttpStatus.INTERNAL_SERVER_ERROR, {})


_request_type_to_post_processor = {}


def _post_processor(request_type: RequestType):
    """
    This decorator factory is used to attach post-processor methods to specific
    RequestTypes.
    """

    def decorator_(func):
        _request_type_to_post_processor[request_type] = func
        return func

    return decorator_


@_post_processor(RequestType.CREATE)
def _create_post_processor(response):
    """
    Post-process CREATE requests.

    The current convention is that service layer functions return True if the
    entity was created and False if the entity already existed, in which case
    nothing was done. When Transiter's PUT requests become more sophisticated
    this may change - see [Github #2].
    """
    return ("", HttpStatus.CREATED if response else HttpStatus.NO_CONTENT, {})


@_post_processor(RequestType.DELETE)
def _delete_post_processor(__):
    """
    Post-process DELETE requests.

    The service layer function always returns True if the delete was successful.
    In all other cases an Exception is raised which is handled in the main
    _process_request method.
    """
    return ("", HttpStatus.NO_CONTENT, {})


@_post_processor(RequestType.GET)
def _get_post_processor(response):
    """
    Post-process GET requests.
    """
    return (
        _convert_to_json_str(response),
        HttpStatus.OK,
        {**HttpHeader.CONTENT_TYPE_JSON.value},
    )


@_post_processor(RequestType.UPDATE)
def _update_post_processor(response):
    """
    Post-process UPDATE requests.
    """
    return (
        _convert_to_json_str(response),
        HttpStatus.CREATED,
        {**HttpHeader.CONTENT_TYPE_JSON.value},
    )


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

    raise TypeError("Type {} not serializable".format(type(obj)))
