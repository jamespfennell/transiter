"""
The sync module is responsible for syncing the results of feed parsers to the database.

This involves:

- Persisting entities in the feed that don't correspond to existing entities.

- Updating existing entities with new data in the feed. In certain cases, for example
    Trips, old data such as past arrival times is preserved.

- Deleting existing entities that no longer appear in the feed.
"""

import typing

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries
from transiter.data.dams import stopdam, tripdam, routedam
from transiter.services.servicemap import servicemapmanager
from transiter.services.update import fastscheduleoperations


def sync(feed_update, entities):
    """
    Sync entities to the database.

    :param feed_update: the feed update event in which this sync operation is being
      performed
    :param entities: the entities to sync
    """

    model_types_sync_order = [
        models.Route,
        models.Stop,
        models.ScheduledService,
        models.Trip,
        models.Alert,
    ]
    model_types = set(model_types_sync_order)
    model_type_to_sync_func = {
        models.Route: _sync_routes,
        models.Stop: _sync_stops,
        models.ScheduledService: _sync_scheduled_services,
        models.Trip: _sync_trips,
        models.Alert: _sync_alerts,
    }

    model_type_to_entities = {model_type: [] for model_type in model_types}
    for entity in entities:
        type_ = type(entity)
        if type_ not in model_types:
            raise TypeError(
                "Object of type {} cannot be synced to the Transiter DB.".format(type_)
            )
        model_type_to_entities[type_].append(entity)

    for model_type in model_types_sync_order:
        model_type_to_sync_func[model_type](
            feed_update, model_type_to_entities[model_type]
        )
        _delete_stale_entities(model_type, feed_update)


def _sync_routes(feed_update, routes):
    if len(routes) == 0:
        return
    persisted_routes = _merge_entities(models.Route, feed_update, routes)
    for route in persisted_routes:
        route.system = feed_update.feed.system


def _sync_stops(feed_update, stops):
    if len(stops) == 0:
        return
    # NOTE: the stop tree is manually linked together because otherwise SQL Alchemy's
    # cascades will result in duplicate entries in the DB because the models do not
    # have PKs yet.
    stop_id_to_parent_stop_id = {
        stop.id: stop.parent_stop.id for stop in stops if stop.parent_stop is not None
    }
    persisted_stops = _merge_entities(models.Stop, feed_update, stops)
    stop_id_to_persisted_stops = {stop.id: stop for stop in persisted_stops}
    for stop in persisted_stops:
        stop.parent_stop = stop_id_to_persisted_stops.get(
            stop_id_to_parent_stop_id.get(stop.id)
        )
        stop.system = feed_update.feed.system


def _sync_scheduled_services(feed_update, services):
    if len(services) > 0:
        persisted_services = _merge_entities(
            models.ScheduledService, feed_update, services
        )
        for service in persisted_services:
            service.system = feed_update.feed.system
    schedule_updated = fastscheduleoperations.sync_trips(feed_update, services)
    if schedule_updated:
        servicemapmanager.calculate_scheduled_service_maps_for_system(
            feed_update.feed.system
        )


def _sync_trips(feed_update, trips):
    if len(trips) == 0:
        return
    session = dbconnection.get_session()
    route_id_to_route = {
        route.id: route
        for route in routedam.list_all_in_system(feed_update.feed.system.id)
    }
    stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(feed_update.feed.system.id)
    trip_id_to_db_trip = {
        trip.id: trip for trip in tripdam.list_all_from_feed(feed_update.feed.pk)
    }

    for feed_trip in trips:
        if len(feed_trip.stop_times) == 0:
            continue
        route = route_id_to_route.get(feed_trip.route_id)
        if route is None:
            continue
        feed_trip.route_pk = route.pk
        feed_trip.source_pk = feed_update.pk

        # Used to ensure that duplicate stops are not put into the DB. This is a
        # safety measure until #36 is resolved.
        future_stop_pks = set()
        for future_stop_time in feed_trip.stop_times:
            stop_pk = stop_id_to_pk.get(future_stop_time.stop_id, None)
            if stop_pk is not None:
                future_stop_pks.add(stop_pk)

        first_future_stop_sequence = feed_trip.stop_times[0].stop_sequence
        feed_stop_times = []
        trip = trip_id_to_db_trip.get(feed_trip.id, None)
        stop_sequence_to_stop_time_pk = {}
        if trip is not None:
            feed_trip.pk = trip.pk
            for stop_time in trip.stop_times:
                stop_sequence_to_stop_time_pk[stop_time.stop_sequence] = stop_time.pk
            # Prepend the trip by all stop times that have a lower stop_sequence
            # and do not contain any stops that are also in the future. This is a
            # safety measure until #36 is resolved.
            for stop_time in trip.stop_times:
                if stop_time.stop_sequence >= first_future_stop_sequence:
                    break
                if stop_time.stop_pk in future_stop_pks:
                    break
                feed_stop_times.append(
                    models.TripStopTime(
                        pk=stop_time.pk,
                        stop_pk=stop_time.stop_pk,
                        future=False,
                        stop_sequence=stop_time.stop_sequence,
                    )
                )
                del stop_sequence_to_stop_time_pk[stop_time.stop_sequence]

        for feed_stop_time in feed_trip.stop_times:
            stop_pk = stop_id_to_pk.get(feed_stop_time.stop_id, None)
            if stop_pk is None:
                continue
            feed_stop_time.stop_pk = stop_pk
            stop_time_pk = stop_sequence_to_stop_time_pk.get(
                feed_stop_time.stop_sequence, None
            )
            if stop_time_pk is not None:
                del stop_sequence_to_stop_time_pk[feed_stop_time.stop_sequence]
            if stop_time_pk is not None:
                feed_stop_time.pk = stop_time_pk

            feed_stop_times.append(feed_stop_time)

        feed_trip.stop_times = feed_stop_times

        session.merge(feed_trip)

    _trigger_service_map_calculations(
        trip_id_to_db_trip.values(), trips, route_id_to_route.values()
    )


def _trigger_service_map_calculations(old_trips, new_trips, routes):
    route_pk_to_route = {route.pk: route for route in routes}
    for route_pk in _calculate_changed_route_pks(old_trips, new_trips):
        servicemapmanager.calculate_realtime_service_map_for_route(
            route_pk_to_route[route_pk]
        )


def _calculate_changed_route_pks(old_trips, new_trips):
    def build_route_pk_to_trip_paths_map(trips):
        route_pk_to_trip_paths = {trip.route_pk: set() for trip in trips}
        for trip in trips:
            if len(trip.stop_times) == 0:
                continue
            if trip.direction_id:
                route_pk_to_trip_paths[trip.route_pk].add(
                    tuple(stop_time.stop_pk for stop_time in trip.stop_times)
                )
            else:
                route_pk_to_trip_paths[trip.route_pk].add(
                    tuple(stop_time.stop_pk for stop_time in reversed(trip.stop_times))
                )
        return route_pk_to_trip_paths

    route_pk_to_old_trip_paths = build_route_pk_to_trip_paths_map(old_trips)
    route_pk_to_new_trip_paths = build_route_pk_to_trip_paths_map(new_trips)
    all_route_pks = set(route_pk_to_new_trip_paths.keys()).union(
        route_pk_to_old_trip_paths.keys()
    )
    changed_route_pks = set()
    for route_pk in all_route_pks:
        old_trip_paths = route_pk_to_old_trip_paths.get(route_pk, set())
        new_trip_paths = route_pk_to_new_trip_paths.get(route_pk, set())
        if old_trip_paths.symmetric_difference(new_trip_paths):
            changed_route_pks.add(route_pk)

    return changed_route_pks


def _sync_alerts(feed_update, alerts):
    if len(alerts) == 0:
        return
    persisted_alerts = _merge_entities(models.Alert, feed_update, alerts)
    route_id_to_route = {route.id: route for route in feed_update.feed.system.routes}
    alert_id_to_route_ids = {alert.id: alert.route_ids for alert in alerts}
    for alert in persisted_alerts:
        alert.routes = [
            route_id_to_route[route_id] for route_id in alert_id_to_route_ids[alert.id]
        ]


# DbEntity is a class
# noinspection PyPep8Naming
def _merge_entities(DbObject: typing.Type[models.Base], feed_update, entities):
    """
    Merge entities of a given type into the session.

    This function will merge entities such that, for example, an existing Alert in
    the feed will not be added but instead its preexisting DB version will be updated.

    :param DbObject: the type of entity to merge
    :param feed_update: the current feed update
    :param entities: the entities to merge
    :return: the persisted entities
    """

    persisted_entities = []
    id_to_pk = genericqueries.get_id_to_pk_map_by_feed_pk(DbObject, feed_update.feed.pk)
    session = dbconnection.get_session()
    for entity in entities:
        if entity.id in id_to_pk:
            entity.pk = id_to_pk[entity.id]
        entity.source_pk = feed_update.pk
        persisted_entities.append(session.merge(entity))

    return persisted_entities


# DbEntity is a class
# noinspection PyPep8Naming
def _delete_stale_entities(DbObject: typing.Type[models.Base], feed_update):
    """
    Remove stale entities from the database.

    A stale entity is currently defined as an entity that was most recently added or
    updated by the feed associated to the current feed update, but that was not
    contained in the current feed update. I.e., it is an entity which previously
    appeared in the current feed of interest but has since disappeared.

    :param DbObject: the type of the entities
    :param feed_update: the current feed update
    """
    session = dbconnection.get_session()
    for entity in genericqueries.list_stale_entities(DbObject, feed_update):
        session.delete(entity)
