from datetime import date, datetime
import json
import time
from decorator import decorator
from transiter.general import linksutil, exceptions as httpexceptions
from ..services import exceptions as serviceexceptions
from transiter.http import permissionsvalidator

# Todo: put these in a class

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_500_SERVER_ERROR = 500
HTTP_501_NOT_IMPLEMENTED = 501

CONTENT_TYPE_JSON = {'Content-Type': 'application/json'}


def create_error_response(msg, status_code):
    json = '{{"error_message": "{}"}}'.format(msg)
    return json, status_code, CONTENT_TYPE_JSON


def _process_request(callback, func, *args, **kw):
    # TODO: make this a dict
    try:
        result = func(*args, **kw)
    except serviceexceptions.IdNotFoundError:
        return '', HTTP_404_NOT_FOUND, ''
    except NotImplementedError:
        return '', HTTP_501_NOT_IMPLEMENTED, ''
    except permissionsvalidator.AccessDenied:
        return '', HTTP_403_FORBIDDEN, ''
    except permissionsvalidator.UnknownPermissionsLevelInRequest:
        return '', HTTP_400_BAD_REQUEST, ''
    except httpexceptions.InvalidJson:
        return create_error_response('Request payload was not valid JSON.', HTTP_400_BAD_REQUEST)
    except httpexceptions.UnexpectedArgument as e:
        return create_error_response(str(e), HTTP_400_BAD_REQUEST)
    except httpexceptions.MissingArgument as e:
        return create_error_response(str(e), HTTP_400_BAD_REQUEST)
    #except Exception as e:
    #    print(e)
    #    return str(e), HTTP_500_SERVER_ERROR, ''

    (content, code) = callback(result)
    return content, code, CONTENT_TYPE_JSON


def _post_process_post(result):
    return convert_to_json(result), HTTP_201_CREATED


def _post_process_get(result):
    return convert_to_json(result), HTTP_200_OK


def _post_process_put(result):
    # NOTE(fennell): put services return true if the resource was
    # created and false otherwise
    if result:
        return '', HTTP_201_CREATED
    else:
        return '', HTTP_204_NO_CONTENT


def _post_process_delete(result):
    return '', HTTP_204_NO_CONTENT


@decorator
def http_get_response(func, *args, **kw):
    return _process_request(_post_process_get, func, *args, **kw)


@decorator
def http_post_response(func, *args, **kw):
    return _process_request(_post_process_post, func, *args, **kw)


@decorator
def http_put_response(func, *args, **kw):
    return _process_request(_post_process_put, func, *args, **kw)


@decorator
def http_delete_response(func, *args, **kw):
    return _process_request(_post_process_delete, func, *args, **kw)


def convert_to_json(data):
    return json.dumps(data, indent=2, separators=(',', ': '), default=json_serial)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    # TODO: options for time formatting
    if isinstance(obj, (datetime, date)):
        return obj.timestamp()
        return (obj.timestamp() - time.time())/60#.isoformat()

    if isinstance(obj, linksutil.Link):
        return obj.url()

    raise TypeError("Type %s not serializable" % type(obj))
