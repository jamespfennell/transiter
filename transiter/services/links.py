import flask
from transiter import models
# TODO: rename links.py

class Link:

    endpoint = None
    kwargs = {}

    def url(self):
        if self.endpoint is None or self.kwargs is None:
            raise NotImplementedError
        http_root = flask.request.headers.get('X-Transiter-HTTP-Root', None)
        if http_root is None:
            return flask.url_for(self.endpoint, _external=True, **self.kwargs)
        else:
            return http_root + flask.url_for(self.endpoint, _external=False, **self.kwargs)

    def __eq__(self, other):
        return (
            self.endpoint == other.endpoint
            and self.kwargs == other.kwargs
        )


class SystemsIndexLink(Link):
    pass


class FeedEntityLink(Link):
    endpoint = 'feed_endpoints.get_in_system_by_id'

    def __init__(self, feed: models.Feed):
        self.kwargs = {
            'system_id': feed.system_id,
            'feed_id': feed.id
        }


class FeedEntityUpdatesLink(Link):
    endpoint = 'feed_endpoints.list_updates_in_feed'

    def __init__(self, feed):
        self.kwargs = {
            'system_id': feed.system_id,
            'feed_id': feed.id
        }


class FeedsInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'feed_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.id
        }


class StopEntityLink(Link):

    def __init__(self, stop):
        self.endpoint = 'stop_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': stop.system_id,
            'stop_id': stop.id
        }


class StopsInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'stop_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.id
        }


class SystemEntityLink(Link):

    def __init__(self, system: models.System):
        self.kwargs = {
            'system_id': system.id,
        }


class RouteEntityLink(Link):

    def __init__(self, route):
        self.endpoint = 'route_endpoints.get_in_system_by_id'
        self.kwargs = {
            'system_id': route.system_id,
            'route_id': route.id
        }


class RoutesInSystemIndexLink(Link):

    def __init__(self, system):
        self.endpoint = 'route_endpoints.list_all_in_system'
        self.kwargs = {
            'system_id': system.id
        }


class TripEntityLink(Link):

    def __init__(self, trip):
        self.endpoint = 'trip_endpoints.get_in_route_by_id'
        self.kwargs = {
            'system_id': trip.route.system_id,
            'route_id': trip.route.id,
            'trip_id': trip.id
        }

