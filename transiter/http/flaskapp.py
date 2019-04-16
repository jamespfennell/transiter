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
    """Provides information about this Transiter instance and the Transit
    systems it contains.

    .. :quickref: Basic instance information

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
    return_links = False
    try:
        commit_hash = (
            subprocess
            .check_output(['git', 'rev-parse', 'HEAD'])
            .decode('utf-8')
            .strip()
        )
    except:
        commit_hash = None
    response = {
        'software': {
            'name': 'Transiter',
            'version': '0.1',
            'commit_hash': commit_hash,
            'href': 'https://github.com/jamespfennell/transiter',
        },
        'systems': {
            'count': 0
        }
    }
    if return_links:
        response['systems']['href'] = linksutil.SystemsIndexLink()
    return response


def launch(force=False):
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
