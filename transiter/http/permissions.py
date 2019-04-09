"""
The permissions module is used to validate that certain HTTP requests have
permission to access a given HTTP resource.

Right now the Transiter permissions system is pretty basic. If works by
inspecting a HTTP header X-Transiter-AllowedMethods to determine what the
minimum allowable permission level is, and for a given resource verifies that
that level is met. The HTTP header is expected to be set by the reverse proxy
(for example, Nginx) that forwards requests to Transiter. This allows only
a subset of Transiter endpoints to be exposed outside the server.

When an administrator needs, they can bypass this system by SSH tunnelling
directly to the Transiter HTTP service.
"""
import enum

import flask

from transiter.general import exceptions


class PermissionsLevel(enum.Enum):
    """
    The allowable permissions levels.

    Transiter permissions level are hierarchical: access to a given level
    permits access to all lower level.
    """
    USER_READ = 0
    ADMIN_READ = 1
    ALL = 2


def ensure(minimum_level):
    """
    Ensure the current HTTP request has sufficient permissions to access a
    resource.

    :param minimum_level: the minimum permissions level required to access the
                          resource
    :type minimum_level: PermissionsLevel
    :raises AccessDenied: if the permissions level is not met
    """
    request_level_str = flask.request.headers.get(
        'X-Transiter-AllowedMethods', PermissionsLevel.ALL.name)
    try:
        request_level = PermissionsLevel[request_level_str.upper()]
    except KeyError:
        raise exceptions.InvalidPermissionsLevelInRequest
    if request_level.value < minimum_level.value:
        raise exceptions.AccessDenied

