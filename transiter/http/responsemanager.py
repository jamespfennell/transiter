import json
from datetime import date, datetime
from decorator import decorator

from transiter.general import linksutil, exceptions # as httpexceptions, exceptions as serviceexceptions

#from requests.status_codes import codes as http_status_code
#
#print(http_status_code.NOT_FOUND)
# Todo: put these in a class or consider using requests.codes

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
    except exceptions.IdNotFoundError:
        return '', HTTP_404_NOT_FOUND, ''
    except NotImplementedError:
        return '', HTTP_501_NOT_IMPLEMENTED, ''
    except exceptions.AccessDenied:
        return '', HTTP_403_FORBIDDEN, ''
    except exceptions.InvalidPermissionsLevelInRequest:
        return '', HTTP_400_BAD_REQUEST, ''
    except exceptions.InvalidJson:
        return create_error_response('Request payload was not valid JSON.', HTTP_400_BAD_REQUEST)
    except exceptions.UnexpectedArgument as e:
        return create_error_response(str(e), HTTP_400_BAD_REQUEST)
    except exceptions.MissingArgument as e:
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
    # NOTE(fennell): PUT services return true if the resource was
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

    if isinstance(obj, (datetime, date)):
        return obj.timestamp()

    if isinstance(obj, linksutil.Link):
        return obj.url()

    raise TypeError("Type %s not serializable" % type(obj))
