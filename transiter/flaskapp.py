from flask import Flask
from .endpoints.systemendpoints import system_endpoints
from .endpoints.routeendpoints import route_endpoints

app = Flask(__name__)
app.register_blueprint(route_endpoints, url_prefix='/systems/<system_id>/routes')
app.register_blueprint(system_endpoints, url_prefix='/systems')


print(app.url_map)
