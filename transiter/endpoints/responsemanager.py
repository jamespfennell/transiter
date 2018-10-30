
from ..utils import jsonutil
from decorator import decorator
from ..services import exceptions
from flask import Response
from transiter.endpoints import permissionsvalidator


# Todo: put these in a class

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_500_SERVER_ERROR = 500
HTTP_501_NOT_IMPLEMENTED = 501


def _process_request(callback, func, *args, **kw):
    try:
        result = func(*args, **kw)
    except exceptions.IdNotFoundError:
        return '', HTTP_404_NOT_FOUND, ''
    except NotImplementedError:
        return '', HTTP_501_NOT_IMPLEMENTED, ''
    except permissionsvalidator.AccessDenied:
        return '', HTTP_403_FORBIDDEN, ''
    except permissionsvalidator.UnknownPermissionsLevelInRequest:
        return '', HTTP_400_BAD_REQUEST, ''
    #except Exception as e:
    #    print(e)
    #    return str(e), HTTP_500_SERVER_ERROR, ''

    (content, code) = callback(result)
    return content, code, {'Content-Type': 'application/json'}


def _post_process_post(result):
    return jsonutil.convert_for_http(result), HTTP_201_CREATED


def _post_process_get(result):
    return jsonutil.convert_for_http(result), HTTP_200_OK


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



