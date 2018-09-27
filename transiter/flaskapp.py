from flask import Flask
from .endpoints.systemendpoints import system_endpoints
from .endpoints.routeendpoints import route_endpoints
#from .endpoints.stopendpoints import stop_endpoints
#from .endpoints.tripendpoints import trip_endpoints
#from .endpoints.feedendpoints import feed_endpoints

app = Flask(__name__)
#app.register_blueprint(feed_endpoints, url_prefix='/systems/<system_id>/feeds')
#app.register_blueprint(stop_endpoints, url_prefix='/systems/<system_id>/stops')
#app.register_blueprint(trip_endpoints, url_prefix='/systems/<system_id>/trips')
app.register_blueprint(route_endpoints, url_prefix='/systems/<system_id>/routes')
app.register_blueprint(system_endpoints, url_prefix='/systems')

@app.route('/')
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
    return 'Not implemented'

@app.route('/about')
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
    return 'Not implemented'




print(app.url_map)
