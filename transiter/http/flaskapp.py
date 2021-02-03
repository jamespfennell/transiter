"""
Entry point and docs
"""
import datetime
import logging

import flask
import pytz
import werkzeug.exceptions as werkzeug_exceptions

from transiter import config, exceptions, __metadata__
from transiter.http import endpoints, httpviews
from transiter.http.httpmanager import (
    http_endpoint,
    HttpStatus,
    convert_exception_to_error_response,
)
from transiter.services import systemservice
from transiter.scheduler import client

app = flask.Flask("transiter", static_folder=None)

app.register_blueprint(endpoints.docs_endpoints, url_prefix="/docs")
app.register_blueprint(endpoints.admin_endpoints, url_prefix="/admin")
app.register_blueprint(
    endpoints.feed_endpoints, url_prefix="/systems/<system_id>/feeds"
)
app.register_blueprint(
    endpoints.agency_endpoints, url_prefix="/systems/<system_id>/agencies"
)
app.register_blueprint(
    endpoints.route_endpoints, url_prefix="/systems/<system_id>/routes"
)
app.register_blueprint(endpoints.stop_endpoints)
app.register_blueprint(endpoints.system_endpoints, url_prefix="/systems")
app.register_blueprint(
    endpoints.transfers_config_endpoints, url_prefix="/admin/transfers-config"
)
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


@app.errorhandler(Exception)
def transiter_error_handler(exception: Exception):
    """
    Error handler for exceptions.
    """
    if not isinstance(exception, exceptions.TransiterException):
        exception = exceptions.UnexpectedError(exception)
    return convert_exception_to_error_response(exception)


@app.errorhandler(HttpStatus.NOT_FOUND)
def page_not_found(__=None):
    """
    What to return if a user requests an endpoint that doesn't exist.
    """
    print(app.root_path)
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
def root():
    """HTTP API entry point

    Provides basic information about this Transiter instance and the Transit
    systems it contains.
    """
    if config.DOCUMENTATION_ENABLED:
        documentation_link = httpviews.InternalDocumentationLink()
    else:
        documentation_link = httpviews.ExternalDocumentationLink()
    response = {
        "transiter": {
            "version": __metadata__.__version__,
            "href": "https://github.com/jamespfennell/transiter",
            "docs": documentation_link,
            "build": _generate_build_response(),
        },
        "systems": httpviews.SystemsInstalled(count=len(systemservice.list_all())),
    }
    return response


@http_endpoint(app, "/metrics", returns_json_response=False)
def metrics():
    """
    Prometheus metrics endpoints

    Provides metrics on feed updating in Prometheus format.
    """
    return client.metrics()


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
