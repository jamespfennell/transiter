"""
Module containing all Exceptions that can be raised in Transiter.
"""
import traceback

import inflection


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


class TransiterException(Exception):
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
            additional_info = {"parameters": self.additional_info}
        else:
            additional_info = {}
        return {
            "type": inflection.underscore(type(self).__name__).upper(),
            "code": self.code,
            "message": self.message,
            **additional_info,
        }

    def __init__(self, message=None):
        super(Exception, self).__init__(message)
        if message is not None:
            self.message = message


class InstallError(TransiterException):
    """
    Exception that is thrown when there's a problem during install.
    """

    code = "T010"
    message = "There was an error installing the transit system."


class UnexpectedError(TransiterException):
    """
    Exception that is thrown when there's a problem during install.
    """

    code = "T011"
    message = (
        "There was an unexpected error. This generally indicates a bug in Transiter"
    )

    def __init__(self, exception=None):
        if exception is not None:
            self.additional_info = {
                "type": type(exception).__name__,
                "message": str(exception),
                # The following formatting makes the stack readable in a browser
                "stack_trace": traceback.format_exc().strip().split("\n"),
            }


class InvalidInput(TransiterException):
    """
    Exception that is thrown when the input to a service layer function is
    invalid. This is usually the result of an invalid user HTTP request.
    """

    code = "T020"
    message = "The request contained invalid input."


class InvalidSystemConfigFile(TransiterException):
    code = "T029"
    message = "The system config file is invalid"


class IdNotFoundError(TransiterException):
    """
    Exception that is raised when a specific DB entity could not be found.
    """

    code = "T050"
    message = "One of the requested entities could not be found."

    def __init__(self, entity_type=None, **kwargs):
        if entity_type is None:
            return
        self.message = f"The {entity_type.__name__.lower()} does not exist."
        self.additional_info = kwargs
        self.additional_info["entity_type"] = entity_type.__name__.lower()


class PageNotFound(TransiterException):
    """
    Exception that is raised when a page cannot be found.
    """

    code = "T051"

    def __init__(self, request_path):
        self.message = "No page found at path '{}'.".format(request_path)
        self.additional_info = {"request_path": request_path}


class MethodNotAllowed(TransiterException):
    """
    Exception that is raised when unsupported method is used.
    """

    code = "T052"
    message = "The requested method is not allowed for this endpoint"

    def __init__(self, request_method, request_path, allowed_methods):
        self.message = (
            "The method {} is not supported for path '{}'. "
            "The allowed methods for this path are: {}."
        ).format(request_method, request_path, ", ".join(allowed_methods))
        self.additional_info = {
            "request_method": request_method,
            "request_path": request_path,
            "allowed_methods": allowed_methods,
        }


class InvalidPermissionsLevelInRequest(TransiterException):
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


class AccessDenied(TransiterException):
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


class InternalDocumentationMisconfigured(TransiterException):
    code = "T070"
    message = "The documentation is currently unavailable"
