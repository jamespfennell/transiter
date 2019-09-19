"""
This module contains the actual Flask app and is a such the 'root' of the HTTP
server. All other HTTP endpoints are linked to the app via blueprints in this
module.
"""
import logging

import flask

from transiter import exceptions, metadata
from transiter.http import endpoints
from transiter.http.httpmanager import http_endpoint, http_response
from transiter.services import links

app = flask.Flask(__name__)

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

logger = logging.getLogger("transiter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter("%(asctime)s WS %(levelname)-5s [%(module)s] %(message)s")
handler.setFormatter(formatter)


@app.errorhandler(404)
@http_response()
def page_not_found(__):
    """
    What to return if a user requests an endpoint that doesn't exist.

    This 404 error is special in that it is the only error that can occur
    outside of our usual endpoint handling. I.e., all other errors like 403
    forbidden arise when we're processing a user request in one of the HTTP
    layer functions and we handle that in the HTTP manager. For this reason
    we don't need special configuration to handle those using Flask.
    """
    raise exceptions.IdNotFoundError


@http_endpoint(app, "/")
def root():
    """Provides information about this Transiter instance and the Transit
    systems it contains.

    .. :quickref: Basic instance information

    :status 200: always
    :return: A JSON response like the following:

    .. code-block:: json

        {
            "software": {
                "name": "Transiter",
                "version": "0.1",
                "href": "https://github.com/jamespfennell/transiter"
            },
            "systems": {
                "count": 1
            }
        }
    """
    return_links = False
    response = {
        "transiter": {
            "version": metadata.VERSION,
            "href": "https://github.com/jamespfennell/transiter",
        },
        "systems": {"count": 0},
    }
    if return_links:
        response["systems"]["href"] = links.SystemsIndexLink()
    return response


def launch(force=False):
    """
    Launch the Flask app in debug mode.

    :param force: unused currently. In future, if true, will force kill any
        process listening on the target port
    """
    logger.setLevel(logging.DEBUG)
    app.run(port=8000, debug=True)
