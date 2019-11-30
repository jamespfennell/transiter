"""
This module contains the actual Flask app and is a such the 'root' of the HTTP
server. All other HTTP endpoints are linked to the app via blueprints in this
module.
"""
import logging

import flask

from transiter import config, exceptions, __version__
from transiter.http import endpoints
from transiter.http.httpmanager import http_endpoint, handle_exceptions
from transiter.services import links, systemservice

app = flask.Flask("transiter")

app.register_blueprint(endpoints.docs_endpoints, url_prefix="/docs")
app.register_blueprint(
    endpoints.feed_endpoints, url_prefix="/systems/<system_id>/feeds"
)
app.register_blueprint(
    endpoints.stop_endpoints, url_prefix="/systems/<system_id>/stops"
)
app.register_blueprint(
    endpoints.route_endpoints, url_prefix="/systems/<system_id>/routes"
)
app.register_blueprint(
    endpoints.trip_endpoints, url_prefix="/systems/<system_id>/routes/<route_id>/trips"
)
app.register_blueprint(endpoints.system_endpoints, url_prefix="/systems")
app.url_map.strict_slashes = False

logger = logging.getLogger("transiter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter("%(asctime)s WS %(levelname)-5s [%(module)s] %(message)s")
handler.setFormatter(formatter)


@app.errorhandler(404)
@handle_exceptions
def page_not_found(__=None):
    """
    What to return if a user requests an endpoint that doesn't exist.

    This 404 error is special in that it is the only error that can occur
    outside of our usual endpoint handling. I.e., all other errors like 403
    forbidden arise when we're processing a user request in one of the HTTP
    layer functions and we handle that in the HTTP manager. For this reason
    we don't need special configuration to handle those using Flask.
    """
    raise exceptions.PageNotFound


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
