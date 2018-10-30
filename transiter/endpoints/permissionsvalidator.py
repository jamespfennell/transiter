from flask import request


class UnknownPermissionsLevelInRequest(Exception):
    def __init__(self, request_level=None):
        self.message = 'Unknown request level in HTTP request "{}".'.format(
            request_level)


class UnknownPermissionsLevelInMethod(Exception):
    def __init__(self, request_level=None):
        self.message = 'Unknown request level in method "{}".'.format(
            request_level)


class AccessDenied(Exception):
    pass


def validate_permissions(method_level):
    level_to_code = {
        'All': 0,
        'AdminRead': 1,
        'UserRead': 2
    }
    request_level = request.headers.get('X-Transiter-AllowedMethods', 'All')
    if request_level not in level_to_code.keys():
        raise UnknownPermissionsLevelInRequest(request_level)
    if method_level not in level_to_code.keys():
        raise UnknownPermissionsLevelInMethod(request_level)
    if level_to_code[method_level] < level_to_code[request_level]:
        raise AccessDenied

