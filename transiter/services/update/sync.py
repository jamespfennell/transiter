"""
The sync module is responsible for syncing the results of feed parsers to the database.

This involves:

- Persisting entities in the feed that don't correspond to existing entities.

- Updating existing entities with new data in the feed. In certain cases, for example
    Trips, old data such as past arrival times is preserved.

- Deleting existing entities that no longer appear in the feed.
"""
import collections
import logging
from typing import Iterable, List, Tuple

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries
from transiter.data.dams import stopdam, tripdam, routedam, scheduledam, feeddam
from transiter.services.servicemap import servicemapmanager
from transiter.services.update import fastscheduleoperations

logger = logging.getLogger(__name__)


def sync(feed_update_pk, entities):
    """
    Sync entities to the database.

    :param feed_update_pk: the feed update event in which this sync operation is being
      performed
    :param entities: the entities to sync
    """
    feed_update = feeddam.get_update_by_pk(feed_update_pk)

    syncers_in_order = [
        RouteSyncer,
        StopSyncer,
        ScheduleSyncer,
        DirectionRuleSyncer,
        TripSyncer,
        AlertSyncer,
    ]
    if feed_update.update_type == feed_update.Type.FLUSH:
        syncers_in_order.reverse()

    model_types = set(syncer.feed_entity() for syncer in syncers_in_order)
    model_type_to_entities = collections.defaultdict(list)
    for entity in entities:
        type_ = type(entity)
        if type_ not in model_types:
            raise TypeError(
                "Object of type {} cannot be synced to the Transiter DB.".format(type_)
            )
        model_type_to_entities[type_].append(entity)
        entity.source_pk = feed_update_pk

    totals = [0, 0, 0]
    for syncer in syncers_in_order:
        logger.debug("Syncing {}".format(syncer.feed_entity()))
        result = syncer(feed_update).run(model_type_to_entities[syncer.feed_entity()])
        for i in range(3):
            totals[i] += result[i]
    return totals


class Syncer:

    __feed_entity__ = None
    __db_entity__ = None

    def __init__(self, feed_update: models.FeedUpdate):
        self.feed_update = feed_update

    def run(self, entities):
        self.pre_sync()
        if len(entities) > 0:
            num_added, num_updated = self.sync(entities)
        else:
            num_added, num_updated = 0, 0
        num_deleted = self.delete_stale_entities()
        self.post_sync()
        return num_added, num_updated, num_deleted

    def pre_sync(self):
        pass

    def sync(self, entities):
        raise NotImplementedError

    def delete_stale_entities(self):
        """
        Remove stale entities from the database.

        A stale entity is currently defined as an entity that was most recently added or
        updated by the feed associated to the current feed update, but that was not
        contained in the current feed update. I.e., it is an entity which previously
        appeared in the current feed of interest but has since disappeared.
        """
        assert self.__db_entity__ is not None
        session = dbconnection.get_session()
        entities_to_delete = genericqueries.list_stale_entities(
            self.__db_entity__, self.feed_update
        )
        for entity in entities_to_delete:
            session.delete(entity)
        return len(entities_to_delete)

    def post_sync(self):
        pass

    @classmethod
    def feed_entity(cls):
        if cls.__feed_entity__ is None:
            return cls.__db_entity__
        return cls.__feed_entity__

    def _merge_entities(self, entities) -> Tuple[list, int, int]:
        """
        Merge entities of a given type into the session.

        This function will merge entities such that, for example, an existing Alert in
        the feed will not be added but instead its preexisting DB version will be updated.

        :param entities: the entities to merge
        :return: the persisted entities
        """

        persisted_entities = []
        id_to_pk = genericqueries.get_id_to_pk_map_by_feed_pk(
            self.__db_entity__, self.feed_update.feed.pk
        )
        session = dbconnection.get_session()
        num_updated_entities = 0
        for entity in entities:
            if entity.id in id_to_pk:
                num_updated_entities += 1
                entity.pk = id_to_pk[entity.id]
            entity.source_pk = self.feed_update.pk
            persisted_entities.append(session.merge(entity))
        return (
            persisted_entities,
            len(entities) - num_updated_entities,
            num_updated_entities,
        )


class RouteSyncer(Syncer):

    __db_entity__ = models.Route

    def sync(self, routes):
        for route in routes:
            route.system_pk = self.feed_update.feed.system_pk
        __, num_added, num_updated = self._merge_entities(routes)
        return num_added, num_updated


class StopSyncer(Syncer):

    __db_entity__ = models.Stop

    def sync(self, stops):
        # NOTE: the stop tree is manually linked together because otherwise SQL
        # Alchemy's cascades will result in duplicate entries in the DB because the
        # models do not have PKs yet.
        stop_id_to_parent_stop_id = {
            stop.id: stop.parent_stop.id
            for stop in stops
            if stop.parent_stop is not None
        }
        for stop in stops:
            stop.system_pk = self.feed_update.feed.system_pk
        persisted_stops, num_added, num_updated = self._merge_entities(stops)
        stop_id_to_persisted_stops = {stop.id: stop for stop in persisted_stops}
        for stop in persisted_stops:
            stop.parent_stop = stop_id_to_persisted_stops.get(
                stop_id_to_parent_stop_id.get(stop.id)
            )
        return num_added, num_updated


class ScheduleSyncer(Syncer):

    __db_entity__ = models.ScheduledService

    recalculate_service_maps = False

    def pre_sync(self):
        num_entities_deleted = fastscheduleoperations.delete_trips_associated_to_feed(
            self.feed_update.feed.pk
        )
        if num_entities_deleted > 0:
            self.recalculate_service_maps = True

    def sync(self, services):
        persisted_services, num_added, num_updated = self._merge_entities(services)
        for service in persisted_services:
            service.system = self.feed_update.feed.system
        schedule_updated = fastscheduleoperations.sync_trips(self.feed_update, services)
        if schedule_updated:
            self.recalculate_service_maps = True
        return num_added, num_updated

    def post_sync(self):
        if not self.recalculate_service_maps:
            return
        servicemapmanager.calculate_scheduled_service_maps_for_system(
            self.feed_update.feed.system
        )


class DirectionRuleSyncer(Syncer):

    __db_entity__ = models.DirectionRule

    def sync(self, direction_rules):
        stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(
            self.feed_update.feed.system.id
        )
        entities_to_merge = []
        for direction_rule in direction_rules:
            stop_pk = stop_id_to_pk.get(direction_rule.stop_id)
            if stop_pk is None:
                continue
            direction_rule.stop_pk = stop_pk
            entities_to_merge.append(direction_rule)

        __, num_added, num_updated = self._merge_entities(entities_to_merge)
        return num_added, num_updated


class TripSyncer(Syncer):
    __feed_entity__ = models.TripLight
    __db_entity__ = models.Trip

    route_pk_to_previous_service_map_hash = {}
    route_pk_to_new_service_map_hash = {}
    stop_time_pks_to_delete = set()

    def sync(self, trips):
        for data_adder in (
            self._add_schedule_data,  # Must come before route data
            self._add_route_data,
            self._add_stop_data,  # Must come before existing trip data
            self._add_existing_trip_data,
        ):
            trips = data_adder(trips)
        self._calculate_route_pk_to_new_service_map_hash(trips)
        return self._fast_merge(trips)

    def _add_schedule_data(self, trips: Iterable[models.Trip]) -> Iterable[models.Trip]:
        """
        Add data to the trip, such as the route, from the schedule.
        """
        trips = list(trips)
        trip_ids_needing_schedule = set()
        for trip in trips:
            route_set = trip.route_pk is not None or trip.route_id is not None
            direction_id_set = trip.direction_id is not None
            if route_set and direction_id_set:
                continue
            trip_ids_needing_schedule.add(trip.id)
        if len(trip_ids_needing_schedule) == 0:
            return trips
        trip_id_to_scheduled_trip = {
            trip.id: trip
            for trip in scheduledam.list_trips_by_system_pk_and_trip_ids(
                self.feed_update.feed.system.pk, trip_ids_needing_schedule
            )
        }
        for trip in trips:
            scheduled_trip = trip_id_to_scheduled_trip.get(trip.id)
            if scheduled_trip is None:
                continue
            trip.route_pk = scheduled_trip.route_pk
            if trip.direction_id is None:
                trip.direction_id = scheduled_trip.direction_id
        return trips

    def _add_route_data(self, trips: Iterable[models.Trip]) -> Iterable[models.Trip]:
        """
        Convert route_ids on the trip into route_pks. Trips that are have invalid
        route IDs and are missing route PKs are filtered out.
        """
        trips = list(trips)
        route_id_to_pk = routedam.get_id_to_pk_map_in_system(
            self.feed_update.feed.system.id,
            [trip.route_id for trip in trips if trip.route_id is not None],
        )
        for trip in trips:
            if trip.route_pk is None:
                trip.route_pk = route_id_to_pk.get(trip.route_id)
                if trip.route_pk is None:
                    continue
            yield trip

    def _add_stop_data(self, trips: Iterable[models.Trip]) -> Iterable[models.Trip]:
        """
        Convert stop_ids on the trip stop times into stop_pks. Trip stop times that have
        invalid stop IDs and are missing stop PKs are filtered out.
        """
        stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(
            self.feed_update.feed.system.id
        )

        def process_stop_times(stop_times):
            for stop_time in stop_times:
                stop_pk = stop_id_to_pk.get(stop_time.stop_id, None)
                if stop_pk is None:
                    continue
                stop_time.stop_pk = stop_pk
                yield stop_time

        for trip in trips:
            trip.stop_times = list(process_stop_times(trip.stop_times))
            yield trip

    def _add_existing_trip_data(
        self, trips: Iterable[models.Trip]
    ) -> Iterable[models.Trip]:
        """
        Add data to the feed trips from data already in the database; i.e., from
        previous feed updates.
        """
        trips = list(trips)
        trip_id_to_db_trip = {
            trip.id: trip
            for trip in tripdam.list_all_from_feed(self.feed_update.feed.pk)
        }
        trip_pk_to_db_stop_time_data_list = tripdam.get_trip_pk_to_stop_time_data_list(
            self.feed_update.feed.pk
        )
        for trip in trips:
            db_trip = trip_id_to_db_trip.get(trip.id, None)
            if db_trip is None:
                continue
            trip.pk = db_trip.pk
            db_stop_time_data = trip_pk_to_db_stop_time_data_list.get(db_trip.pk, [])
            past_stop_times_iter = self._build_past_stop_times(
                trip, db_trip, db_stop_time_data
            )
            self._add_future_stop_time_data_to_trip(trip, db_stop_time_data)
            trip.stop_times = list(past_stop_times_iter) + trip.stop_times

        self._calculate_stop_time_pks_to_delete(
            trips, trip_pk_to_db_stop_time_data_list
        )
        self._calculate_route_pk_to_previous_service_map_hash(
            trip_id_to_db_trip.values(), trip_pk_to_db_stop_time_data_list
        )
        return trips

    @staticmethod
    def _build_past_stop_times(
        trip, db_trip, db_stop_time_data_list: List[tripdam.StopTimeData]
    ) -> Iterable[models.TripStopTimeLight]:
        """
        Build stop times that have already passed and are not in the feed.
        """
        if db_trip is None:
            return
        if len(trip.stop_times) == 0:
            return
        first_future_stop_sequence = trip.stop_times[0].stop_sequence
        # Used to ensure that duplicate stops are not put into the DB. This is a
        # safety measure until #36 is resolved.
        future_stop_pks = set(stop_time.stop_pk for stop_time in trip.stop_times)
        for stop_time_data in db_stop_time_data_list:
            if stop_time_data.stop_sequence >= first_future_stop_sequence:
                return
            if stop_time_data.stop_pk in future_stop_pks:
                return
            past_stop_time = models.TripStopTime.from_feed(
                trip_id=trip.id,
                stop_id="temporary_placeholder",
                stop_sequence=stop_time_data.stop_sequence,
                future=False,
            )
            past_stop_time.stop_pk = stop_time_data.stop_pk
            past_stop_time.pk = stop_time_data.pk
            yield past_stop_time

    @staticmethod
    def _add_future_stop_time_data_to_trip(trip, db_stop_time_data):
        """
        Add stop time data from the database trip.
        """
        stop_sequence_to_pk_and_stop_pk = {
            stop_sequence: (stop_time_pk, stop_pk)
            for stop_time_pk, stop_sequence, stop_pk in db_stop_time_data
        }
        for feed_stop_time in trip.stop_times:
            stop_time_pk, __ = stop_sequence_to_pk_and_stop_pk.get(
                feed_stop_time.stop_sequence, (None, None)
            )
            if stop_time_pk is not None:
                feed_stop_time.pk = stop_time_pk

    def _calculate_stop_time_pks_to_delete(self, trips, trip_pk_to_db_stop_time_data):
        """
        Calculate the stop time pks to delete and store them in the object variable.
        """
        updated_stop_time_pks = set(
            stop_time.pk
            for trip in trips
            for stop_time in trip.stop_times
            if stop_time.pk is not None
        )
        self.stop_time_pks_to_delete = set(
            stop_time_data.pk
            for db_stop_time_data_list in trip_pk_to_db_stop_time_data.values()
            for stop_time_data in db_stop_time_data_list
            if stop_time_data.pk not in updated_stop_time_pks
        )

    def _calculate_route_pk_to_previous_service_map_hash(
        self, db_trips, trip_pk_to_db_stop_time_data_list
    ):
        """
        Calculate the previous service map information and store it in the object
        variable.
        """
        route_pk_to_trip_paths = collections.defaultdict(set)
        for db_trip in db_trips:
            db_stop_time_data_list = trip_pk_to_db_stop_time_data_list.get(
                db_trip.pk, []
            )
            if len(db_stop_time_data_list) == 0:
                continue
            if not db_trip.direction_id:
                db_stop_time_data_list = reversed(db_stop_time_data_list)
            route_pk_to_trip_paths[db_trip.route_pk].add(
                tuple(
                    stop_time_data.stop_pk for stop_time_data in db_stop_time_data_list
                )
            )
        self.route_pk_to_previous_service_map_hash = {
            route_pk: servicemapmanager.calculate_paths_hash(paths)
            for route_pk, paths in route_pk_to_trip_paths.items()
        }

    def _calculate_route_pk_to_new_service_map_hash(self, trips):
        """
        Calculate the new service map information and store it in the object
        variable.
        """
        route_pk_to_trip_paths = collections.defaultdict(set)
        for trip in trips:
            if len(trip.stop_times) == 0:
                continue
            if trip.direction_id:
                stop_times = trip.stop_times
            else:
                stop_times = reversed(trip.stop_times)
            route_pk_to_trip_paths[trip.route_pk].add(
                tuple(stop_time.stop_pk for stop_time in stop_times)
            )
        self.route_pk_to_new_service_map_hash = {
            route_pk: servicemapmanager.calculate_paths_hash(paths)
            for route_pk, paths in route_pk_to_trip_paths.items()
        }

    def _fast_merge(self, trips):
        num_added, num_updated = self._fast_mappings_merge(models.Trip, trips)
        trip_id_to_db_trip_pk = genericqueries.get_id_to_pk_map_by_feed_pk(
            models.Trip, self.feed_update.feed.pk
        )
        dbconnection.get_session().query(models.TripStopTime).filter(
            models.TripStopTime.pk.in_(self.stop_time_pks_to_delete)
        ).delete(synchronize_session=False)
        for trip in trips:
            trip_pk = trip_id_to_db_trip_pk[trip.id]
            for stop_time in trip.stop_times:
                stop_time.trip_pk = trip_pk
        self._fast_mappings_merge(
            models.TripStopTime,
            (stop_time for trip in trips for stop_time in trip.stop_times),
        )
        return num_added, num_updated

    @staticmethod
    def _fast_mappings_merge(db_model, entities):
        new_mappings = []
        updated_mappings = []
        for entity in entities:
            mapping = entity.to_mapping()
            if mapping["pk"] is not None:
                updated_mappings.append(mapping)
            else:
                del mapping["pk"]
                new_mappings.append(mapping)
        session = dbconnection.get_session()
        session.bulk_insert_mappings(db_model, new_mappings)
        session.bulk_update_mappings(db_model, updated_mappings)
        session.flush()
        return len(new_mappings), len(updated_mappings)

    def post_sync(self):
        changed_route_pks = servicemapmanager.calculate_changed_route_pks_from_hashes(
            self.route_pk_to_previous_service_map_hash,
            self.route_pk_to_new_service_map_hash,
        )
        if len(changed_route_pks) == 0:
            return
        route_pk_to_route = {
            route.pk: route
            for route in routedam.list_all_in_system(self.feed_update.feed.system.id)
        }
        for route_pk in changed_route_pks:
            servicemapmanager.calculate_realtime_service_map_for_route(
                route_pk_to_route[route_pk]
            )


class AlertSyncer(Syncer):

    __db_entity__ = models.Alert

    def sync(self, alerts):
        persisted_alerts, num_added, num_updated = self._merge_entities(alerts)
        route_id_to_route = {
            route.id: route for route in self.feed_update.feed.system.routes
        }
        alert_id_to_route_ids = {
            alert.id: alert.route_ids for alert in alerts if alert.route_ids is not None
        }
        alert_id_to_agency_ids = {
            alert.id: alert.agency_ids
            for alert in alerts
            if alert.agency_ids is not None
        }
        for alert in persisted_alerts:
            alert.routes = [
                route_id_to_route[route_id]
                for route_id in alert_id_to_route_ids.get(alert.id, [])
            ]
            # NOTE: this is a temporary thing pending the creation of models.Agency
            if len(alert_id_to_agency_ids.get(alert.id, [])) > 0:
                alert.system_pk = self.feed_update.feed.system.pk
        return num_added, num_updated
