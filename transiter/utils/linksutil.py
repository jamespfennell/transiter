from transiter.database import models
import flask


class Link:

    endpoint = None
    kwargs = None

    def url(self):
        if self.endpoint is None or self.kwargs is None:
            raise NotImplementedError
        return flask.url_for(self.endpoint, _external=True, **self.kwargs)


class FeedEntityLink(Link):

    def __init__(self, feed):
        self.endpoint = 'feed_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': feed.system_id,
            'feed_id': feed.feed_id
        }


class FeedsInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'feed_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.system_id
        }


class StopEntityLink(Link):

    def __init__(self, stop):
        self.endpoint = 'stop_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': stop.system_id,
            'stop_id': stop.stop_id
        }


class StopsInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'stop_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.system_id
        }


class SystemEntityLink(Link):

    def __init__(self, system):
        self.endpoint = 'system_endpoints.get_by_id'
        self.kwargs = {
            'system_id': system.system_id,
        }


class RouteEntityLink(Link):

    def __init__(self, route):
        self.endpoint = 'route_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': route.system_id,
            'route_id': route.route_id
        }


class RoutesInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'route_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.system_id
        }


class TripEntityLink(Link):

    def __init__(self, trip):
        self.endpoint = 'trip_endpoints.get_in_route_by_id'
        self.kwargs = {
            'system_id': trip.route.system_id,
            'route_id': trip.route.route_id,
            'trip_id': trip.trip_id
        }
