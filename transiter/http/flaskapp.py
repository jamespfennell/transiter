"""
This module contains the actual Flask app and is a such the 'root' of the HTTP
server. All other HTTP endpoints are linked to the app via blueprints in this
module.
"""
import datetime
import logging

import flask
import pytz
import werkzeug.exceptions as werkzeug_exceptions

from transiter import config, exceptions, __metadata__
from transiter.http import endpoints
from transiter.http.httpmanager import (
    http_endpoint,
    HttpStatus,
    convert_exception_to_error_response,
)
from transiter.services import links, systemservice

app = flask.Flask("transiter")

app.register_blueprint(endpoints.docs_endpoints, url_prefix="/docs")
app.register_blueprint(endpoints.admin_endpoints, url_prefix="/admin")
app.register_blueprint(
    endpoints.feed_endpoints, url_prefix="/systems/<system_id>/feeds"
)
app.register_blueprint(
    endpoints.route_endpoints, url_prefix="/systems/<system_id>/routes"
)
app.register_blueprint(
    endpoints.stop_endpoints, url_prefix="/systems/<system_id>/stops"
)
app.register_blueprint(endpoints.system_endpoints, url_prefix="/systems")
app.register_blueprint(
    endpoints.trip_endpoints, url_prefix="/systems/<system_id>/routes/<route_id>/trips"
)
app.url_map.strict_slashes = False

logger = logging.getLogger("transiter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter("%(asctime)s WS %(levelname)-5s [%(module)s] %(message)s")
handler.setFormatter(formatter)


@app.errorhandler(exceptions.TransiterException)
def transiter_error_handler(exception: exceptions.TransiterException):
    """
    Error handler for Transiter exceptions.
    """
    return convert_exception_to_error_response(exception)


@app.errorhandler(HttpStatus.NOT_FOUND)
def page_not_found(__=None):
    """
    What to return if a user requests an endpoint that doesn't exist.
    """
    return transiter_error_handler(exceptions.PageNotFound(flask.request.path))


@app.errorhandler(HttpStatus.METHOD_NOT_ALLOWED)
def method_not_allowed(werkzeug_exception: werkzeug_exceptions.MethodNotAllowed):
    """
    What to return if a user requests an endpoint with a disallowed method.
    """
    return transiter_error_handler(
        exceptions.MethodNotAllowed(
            flask.request.method, flask.request.path, werkzeug_exception.valid_methods
        )
    )


@http_endpoint(app, "/")
def root(return_links=True):
    """HTTP/REST API entry point.

    Provides basic information about this Transiter instance and the Transit
    systems it contains.
    """
    response = {
        "transiter": {
            "version": __metadata__.__version__,
            "href": "https://github.com/jamespfennell/transiter",
            "build": _generate_build_response(),
        },
        "systems": {"count": len(systemservice.list_all())},
    }
    if return_links:
        if config.DOCUMENTATION_ENABLED:
            documentation_link = links.InternalDocumentationLink()
        else:
            documentation_link = "https://docs.transiter.io"
        response["transiter"]["docs"] = {"href": documentation_link}
        response["systems"]["href"] = links.SystemsIndexLink()
    return response


def _generate_build_response():
    if __metadata__.__build_number__ is None:
        return None
    human_time = (
        datetime.datetime.fromtimestamp(
            __metadata__.__build_timestamp__, pytz.timezone("US/Eastern")
        ).isoformat()
        if __metadata__.__build_timestamp__ is not None
        else None
    )
    return {
        "number": __metadata__.__build_number__,
        "built_at": human_time,
        "built_at_timestamp": __metadata__.__build_timestamp__,
        "git_commit_hash": __metadata__.__git_commit_hash__,
        "href": __metadata__.__build_href__,
    }


def launch(force=False):
    """
    Launch the Flask app in debug mode.
    """
    logger.setLevel(logging.DEBUG)
    app.run(port=8000, debug=True)
