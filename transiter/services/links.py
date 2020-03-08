"""
Module containing Links.

These objects are used in service layer responses to represent,
abstractly, a link to another entity. The HTTP layer then converts these
link objects to concrete URLs.
"""

from transiter import models


class Link:
    kwargs = {}

    def __eq__(self, other):
        return type(self) == type(other) and self.kwargs == other.kwargs


class InternalDocumentationLink(Link):
    pass


class SystemsIndexLink(Link):
    pass


class FeedEntityLink(Link):
    def __init__(self, feed: models.Feed):
        self.kwargs = {"system_id": feed.system.id, "feed_id": feed.id}


class FeedEntityUpdatesLink(Link):
    def __init__(self, feed: models.Feed):
        self.kwargs = {"system_id": feed.system.id, "feed_id": feed.id}


class FeedsInSystemIndexLink(Link):
    def __init__(self, system: models.System):
        self.kwargs = {"system_id": system.id}


class StopEntityLink(Link):
    def __init__(self, stop: models.Stop):
        self.kwargs = {"system_id": stop.system.id, "stop_id": stop.id}


class StopsInSystemIndexLink(Link):
    def __init__(self, system: models.System):
        self.kwargs = {"system_id": system.id}


class SystemEntityLink(Link):
    def __init__(self, system: models.System):
        self.kwargs = {"system_id": system.id}


class RouteEntityLink(Link):
    def __init__(self, route: models.Route):
        self.kwargs = {"system_id": route.system.id, "route_id": route.id}


class RoutesInSystemIndexLink(Link):
    def __init__(self, system: models.System):
        self.kwargs = {"system_id": system.id}


class TripEntityLink(Link):
    def __init__(self, trip: models.Trip):
        self.kwargs = {
            "system_id": trip.route.system.id,
            "route_id": trip.route.id,
            "trip_id": trip.id,
        }
