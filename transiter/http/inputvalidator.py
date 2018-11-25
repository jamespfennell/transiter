from flask import request
from transiter.http import exceptions


def validate_post_data(required_fields, optional_fields):
    json = request.get_json(force=True, silent=True)
    if json is None:
        raise exceptions.InvalidJson()
    return validate_json(json, required_fields, optional_fields)


def validate_get_data(required_fields, optional_fields):
    return validate_json(request.args, required_fields, optional_fields)


def validate_json(content, required_fields, optional_fields):

    for required_field in required_fields:
        if required_field not in content.keys():
            raise exceptions.MissingArgument('Missing an expected argument \'{}\'.'.format(required_field))

    for content_field in content.keys():
        if (content_field not in required_fields and
                content_field not in optional_fields):
            raise exceptions.UnexpectedArgument('Received an unexpected argument \'{}\'.'.format(content_field))

    return content

