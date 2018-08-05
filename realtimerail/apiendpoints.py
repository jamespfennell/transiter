


@app.route('api/routes/<string:route_id>')
def get_route(route_id):
    return routeService().get_by_id(route_id)

@app.route('api/routes')
def list_routes():
    return routeService().list()

# This pattern ^ is the same for stop and trip and feed


@app.route('api/<string:feed_id>/update')
def update_feed(feed_id):
    return feedService().update_feed(feed_id)
