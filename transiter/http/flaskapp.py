import logging
import subprocess

from flask import Flask

from transiter.http.endpoints.feedendpoints import feed_endpoints
from transiter.http.endpoints.routeendpoints import route_endpoints
from transiter.http.endpoints.stopendpoints import stop_endpoints
from transiter.http.endpoints.systemendpoints import system_endpoints
from transiter.http.endpoints.tripendpoints import trip_endpoints
from transiter.http.responsemanager import http_get_response
from transiter.general import linksutil

app = Flask(__name__)
app.register_blueprint(feed_endpoints, url_prefix='/systems/<system_id>/feeds')
app.register_blueprint(stop_endpoints, url_prefix='/systems/<system_id>/stops')
app.register_blueprint(route_endpoints, url_prefix='/systems/<system_id>/routes')
app.register_blueprint(trip_endpoints, url_prefix='/systems/<system_id>/routes/<route_id>/trips')
app.register_blueprint(system_endpoints, url_prefix='/systems')


@app.errorhandler(404)
def page_not_found(__):
    return '', 404


@app.route('/')
@http_get_response
def root():
    """Provides links to the root resources.

     This response is mostly to be consistent with the REST links
     convention, and allows users to 'explore' the API.

    .. :quickref: Basic entry info

    :status 200: always
    :return: A JSON response like the following:

    .. code-block:: json

        {
            "about": {
                "href": "https://demo.transiter.io/about"
            },
            "systems": {
                "href": "https://demo.transiter.io/systems"
            }
        }
    """
    return {
        'about': {
            'href': linksutil.AboutLink()
        },
        'systems': {
            'href': linksutil.SystemsIndexLink()
        }
    }


@app.route('/about')
@http_get_response
def about():
    """Get basic information about this Transiter instance.

    As well as providing generic information like the Github link,
    this endpoint returns the current version and Git commit hash, for
    debugging purposes.

    .. :quickref: About; Information about this Transiter instance.

    :status 200: always
    :return: A JSON response like the following:

    .. code-block:: json

        {
            "name": "Transiter",
            "version": "0.1",
            "commit": "f58cde22b4532dd493fc65c8fefe8aaba562e28e",
            "href": "https://github.com/jamespfennell/transiter",
            "licence": {
                "name": "MIT Licence",
                "href": "https://github.com/jamespfennell/transiter/blob/master/LICENSE"
            }
        }
    """
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except:
        commit_hash = 'Not available'
    return {
        "name": "Transiter",
        "version": "0.1",
        "commit": commit_hash,
        "href": "https://github.com/jamespfennell/transiter",
        "licence": {
            "name": "MIT Licence",
            "href": "https://github.com/jamespfennell/transiter/blob/master/LICENSE"
        },
    }


def launch():
    logger = logging.getLogger('transiter')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s WS %(levelname)-5s [%(module)s] %(message)s')
    handler.setFormatter(formatter)

    app.run(debug=True)


if __name__ == '__main__':
    launch()
