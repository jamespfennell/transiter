
class ConfigFileNotFoundError(Exception):
    pass


# TODO: accept the ID and type and make a better warning
class IdNotFoundError(Exception):
    pass


class InvalidJson(Exception):
    pass


class UnexpectedArgument(Exception):
    pass


class MissingArgument(Exception):
    pass


#Permissions related:

class InvalidPermissionsLevelInRequest(Exception):
    def __init__(self, request_level=None):
        self.message = 'Unknown request level in HTTP request "{}".'.format(
            request_level)


class AccessDenied(Exception):
    pass