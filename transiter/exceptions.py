"""
Module containing all Exceptions that can be raised in Transiter.
"""


# NOTE: All exceptions in this module have two requirements:
#
# (1) They must be subclasses of _TransiterException.
#
# (2) They must have an associated HTTP TripStatus in the HTTP Manager.
#
# If an exception is added breaking one of these, one of the HTTP Manager
# unit tests will very intentionally fail.
#
# NOTE: (2) may potentially be revisited if there are exceptions that are
# never expected to make it to the HTTP layer. Another idea is to permit any
# ancestor of the exception to have a HTTP status.


class _TransiterException(Exception):
    """
    Base exception for all Transiter exceptions.
    """

    code = None
    message = None
    additional_info = {}

    def response(self):
        """
        Return structured information about this exception instance.
        """
        if len(self.additional_info) > 0:
            additional_info = {"additional_info": self.additional_info}
        else:
            additional_info = {}
        return {
            "type": type(self).__name__,
            "code": self.code,
            "message": self.message,
            **additional_info,
        }

    def __init__(self, message=None):
        if message is not None:
            self.message = message


class InstallError(_TransiterException):
    """
    Exception that is thrown when there's a problem during install.
    """

    code = "T010"
    message = "There was an error installing the transit system."


class InvalidInput(_TransiterException):
    """
    Exception that is thrown when the input to a service layer function is
    invalid. This is usually the result of an invalid user HTTP request.
    """

    code = "T020"
    message = "The request contained invalid input."


class InvalidSystemConfigFile(_TransiterException):
    code = "T029"
    message = "The system config file is invalid"


class ConfigFileNotFoundError(_TransiterException):
    """
    Exception that is raised when the Transiter config file could not be found.
    """

    code = "T030"
    message = "The Transiter config file could not be found!"


class IdNotFoundError(_TransiterException):
    """
    Exception that is raised when a specific DB entity could not be found.
    """

    code = "T050"
    message = "One of the requested entities could not be found."


class InvalidPermissionsLevelInRequest(_TransiterException):
    """
    Raised when the HTTP requests contains an unknown permissions level.
    """

    code = "T060"

    def __init__(self, permissions_level_str=None, valid_levels=[]):
        self.message = "Unknown permissions level in the HTTP request."
        self.additional_info = {
            "request_permissions_level": permissions_level_str,
            "valid_permissions_levels": valid_levels,
        }


class AccessDenied(_TransiterException):
    """
    Raised when the HTTP request has insufficient permissions.
    """

    code = "T061"

    def __init__(self, provided=None, required=None):
        self.message = "Insufficient permission to access this HTTP endpoint."
        self.additional_info = {
            "required_permissions_level": required,
            "request_permissions_level": provided,
        }
