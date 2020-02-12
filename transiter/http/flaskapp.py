"""
This module contains the actual Flask app and is a such the 'root' of the HTTP
server. All other HTTP endpoints are linked to the app via blueprints in this
module.
"""
import logging

import flask
import werkzeug.exceptions as werkzeug_exceptions

from transiter import config, exceptions, __version__
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
            "version": __version__.__version__,
            "href": "https://github.com/jamespfennell/transiter",
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


def launch(force=False):
    """
    Launch the Flask app in debug mode.
    """
    logger.setLevel(logging.DEBUG)
    app.run(port=8000, debug=True)
