from flask import Flask
from transiter.http.endpoints.systemendpoints import system_endpoints
from transiter.http.endpoints.routeendpoints import route_endpoints
from transiter.http.endpoints.stopendpoints import stop_endpoints
from transiter.http.endpoints.tripendpoints import trip_endpoints
from transiter.http.endpoints.feedendpoints import feed_endpoints
from transiter.http.responsemanager import http_get_response

app = Flask(__name__)
app.register_blueprint(feed_endpoints, url_prefix='/systems/<system_id>/feeds')
app.register_blueprint(stop_endpoints, url_prefix='/systems/<system_id>/stops')
app.register_blueprint(route_endpoints, url_prefix='/systems/<system_id>/routes')
app.register_blueprint(trip_endpoints, url_prefix='/systems/<system_id>/routes/<route_id>/trips')
app.register_blueprint(system_endpoints, url_prefix='/systems')


@app.route('/')
@http_get_response
def root():
    """Basic entry info

    .. :quickref: Basic entry info

    :status 200: always
    :return: A JSON response like the following:

    .. code-block:: json

        {
            "about": {
                "href": "https://transiter.io/about"
            },
            "systems": {
                "href": "https://transiter.io/systems"
            }
        }
    """
    return {
        'about': {
            'href': 'Not implemented'
        },
        'systems': {
            'href': 'Not implemented'
        }
    }


@app.route('/about')
@http_get_response
def about():
    """Get information about this Transiter instance.

    .. :quickref: About; Information about this Transiter instance.

    :status 200: always
    :return: A JSON response like the following:

    .. code-block:: json

        {
            "name": "Transiter",
            "version": "0.1",
            "source": {
                "licence": {
                    "name": "MIT Licence",
                    "href": "https://github.com/jamespfennell/transiter/blob/master/LICENSE"
                },
                "href": "https://github.com/jamespfennell/transiter"
            }
        }
    """
    return {
        "name": "Transiter",
        "version": "0.1",
        "source": {
            "licence": {
                "name": "MIT Licence",
                "href": "https://github.com/jamespfennell/transiter/blob/master/LICENSE"
            },
            "href": "https://github.com/jamespfennell/transiter"
        }
    }


if __name__ == '__main__':
    app.run(debug=True)
