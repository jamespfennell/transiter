
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