import dataclasses
import itertools
import typing

from transiter import parse
from transiter.db import dbconnection, models
from transiter.db.queries import genericqueries, schedulequeries


def sync_trips(feed_update, parsed_services: typing.List[parse.ScheduledService]):
    num_entities_deleted = delete_trips_associated_to_feed(feed_update.feed.pk)
    if len(parsed_services) == 0:
        return num_entities_deleted > 0

    session = dbconnection.get_session()

    service_id_to_pk = genericqueries.get_id_to_pk_map_by_feed_pk(
        models.ScheduledService, feed_update.feed.pk
    )
    route_id_to_pk = genericqueries.get_id_to_pk_map(
        models.Route, feed_update.feed.system.pk
    )
    trip_mappings = []
    for parsed_service in parsed_services:
        for trip in parsed_service.trips:
            trip_mappings.append(
                {
                    "id": trip.id,
                    "route_pk": route_id_to_pk[trip.route_id],
                    "service_pk": service_id_to_pk[parsed_service.id],
                    "direction_id": trip.direction_id,
                    "headsign": trip.headsign,
                    "short_name": trip.short_name,
                    "wheelchair_accessible": trip.wheelchair_accessible,
                    "bikes_allowed": trip.bikes_allowed,
                }
            )
    session.bulk_insert_mappings(models.ScheduledTrip, trip_mappings)

    trip_id_to_pk = schedulequeries.get_trip_id_to_pk_map_by_feed_pk(
        feed_update.feed.pk
    )

    stop_id_to_pk = genericqueries.get_id_to_pk_map(
        models.Stop, feed_update.feed.system.pk
    )
    # NOTE: SQL Alchemy's bulk_insert_mappings can take up a huge amount of memory if
    # executed on a large collection of mappings. If executed on the NYC Subway's
    # collection of stop times, it uses up to 750mb of memory. Chunking solves this
    # and actually seems to make the process faster.
    all_trips_iter = itertools.chain.from_iterable(
        parsed_service.trips for parsed_service in parsed_services
    )
    for chunk_of_trips in split(all_trips_iter, 100):
        stop_time_mappings = []
        frequency_mappings = []
        for trip in chunk_of_trips:
            for trip_frequency in trip.frequencies:
                frequency_mappings.append(
                    {
                        "trip_pk": trip_id_to_pk[trip.id],
                        **dataclasses.asdict(trip_frequency),
                    }
                )
            for stop_time in trip.stop_times:
                if stop_time.stop_id not in stop_id_to_pk:
                    continue
                stop_time_mappings.append(
                    {
                        "trip_pk": trip_id_to_pk[trip.id],
                        "stop_pk": stop_id_to_pk[stop_time.stop_id],
                        "arrival_time": stop_time.arrival_time,
                        "departure_time": stop_time.departure_time,
                        "stop_sequence": stop_time.stop_sequence,
                        "headsign": stop_time.headsign,
                        "pickup_type": stop_time.pickup_type,
                        "drop_off_type": stop_time.drop_off_type,
                        "continuous_pickup": stop_time.continuous_pickup,
                        "continuous_drop_off": stop_time.continuous_drop_off,
                        "shape_distance_traveled": stop_time.shape_distance_traveled,
                        "exact_times": stop_time.exact_times,
                    }
                )
        session.bulk_insert_mappings(models.ScheduledTripStopTime, stop_time_mappings)
        if len(frequency_mappings) > 0:
            session.bulk_insert_mappings(
                models.ScheduledTripFrequency, frequency_mappings
            )

    return num_entities_deleted > 0 or len(trip_mappings) > 0


def split(container, size):
    chunk = []
    for index, element in enumerate(container):
        chunk.append(element)
        if (index + 1) % size == 0:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk


def delete_trips_associated_to_feed(feed_pk):
    session = dbconnection.get_session()
    base_queries = [
        session.query(models.ScheduledTripStopTime).filter(
            models.ScheduledTrip.pk == models.ScheduledTripStopTime.trip_pk
        ),
        session.query(models.ScheduledTripFrequency).filter(
            models.ScheduledTrip.pk == models.ScheduledTripFrequency.trip_pk
        ),
        session.query(models.ScheduledTrip),
    ]
    num_deleted = 0
    for base_query in base_queries:
        num_deleted += base_query.filter(
            models.ScheduledService.pk == models.ScheduledTrip.service_pk,
            models.FeedUpdate.pk == models.ScheduledService.source_pk,
            models.FeedUpdate.feed_pk == feed_pk,
        ).delete(synchronize_session=False)
    return num_deleted
