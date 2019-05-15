"""
The GTFS Realtime Util contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/realtime/v2/
"""
import datetime
import time

import pytz
from google.transit import gtfs_realtime_pb2

from transiter import models
from transiter.services.update import tripupdater


def create_parser(
    gtfs_realtime_pb2_module=None,
    post_pb2_parsing_function=None,
    trip_data_cleaner: tripupdater.TripDataCleaner = None,
    route_ids_function=None,
):
    """
    Create a GTFS Realtime parser.

    The returned parser performs the following steps in order:

    (1) Read the GTFS Realtime binary data into a JSON structure using either
        the default GTFS Realtime protobuf modules or a custom module.
        The custom is for when a GTFS Realtime extension is being used.

    (2) Optionally apply a post-pb2-parsing function to the JSON structure.
        This is generally use for merging GTFS Realtime extension data into
        the main JSON structure. Clean-up of the data within the feed is
        easier with a trip cleaner in (4).

    (3) Convert the JSON structure into various Transiter Python objects.
        These objects are SQL Alchemy models that correspond to database tables.

    (4) Optionally apply a trip cleaner to the Python objects to filter out
        bad trips or otherwise clean up the data.

    (5) Persist the Python objects in the database.

    :param gtfs_realtime_pb2_module: optional, the protobuffers module to use
        to read the feed. Defaults to the official module on PyPI.
    :param post_pb2_parsing_function: the function described in (2). It takes
        a single argument, which is the JSON data structure. It returns nothing;
        rather, it alterts the JSON structure in place.
    :param trip_data_cleaner: the trip cleaner described in (4)
    :param route_ids_function: a function used to determine which routes are
        update as part of this feed update. It takes in two arguments
        (route_ids, feed) where route_ids is the collection or route_ids
        found in the feed. Defaults to returning all routes in the system.
    :return: the parser
    """
    if gtfs_realtime_pb2_module is None:
        gtfs_realtime_pb2_module = gtfs_realtime_pb2
    if post_pb2_parsing_function is None:
        post_pb2_parsing_function = lambda __: None
    if trip_data_cleaner is None:
        trip_data_cleaner_function = lambda __, trips: trips
    else:
        trip_data_cleaner_function = trip_data_cleaner.clean
    if route_ids_function is None:
        route_ids_function = lambda __, ___: None

    def parser(feed_update, content):
        gtfs_data = read_gtfs_realtime(content, gtfs_realtime_pb2_module)
        post_pb2_parsing_function(gtfs_data)
        (feed_time, route_ids, trips) = transform_to_transiter_structure(
            gtfs_data, "America/New_York"
        )
        feed_update.feed_time = feed_time
        cleaned_trips = trip_data_cleaner_function(feed_update, trips)
        tripupdater.sync_trips(
            feed_update.feed.system,
            cleaned_trips,
            route_ids_function(feed_update.feed, route_ids),
        )

    return parser


built_in_parser = create_parser()


def read_gtfs_realtime(content, gtfs_realtime_pb2_module):
    """
    Convert a binary GTFS Realtime feed to a JSON-like data structure

    :param content: GTFS realtime binary data
    :param gtfs_realtime_pb2_module: GTFS realtime module
    :return: the data in a JSON-like data structure
    """
    gtfs_feed = gtfs_realtime_pb2_module.FeedMessage()
    gtfs_feed.ParseFromString(content)
    return _read_protobuf_message(gtfs_feed)


def _read_protobuf_message(message):
    """
    Convert a protobuf message into a JSON-like structure.

    This is not an exhaustive converter but mean to be sufficient for GTFS
    realtime

    :param message: a google.protobuf.message.Message object
    :return: a dictionary of {key: value} for fields in the Message. The
    function is recursive so if value is also a protobuf then that will be
    expanded
    """
    d = {}
    for (descriptor, value) in message.ListFields():
        # Iterate through the possible protobuf field types to decide how to
        # parse this value
        if descriptor.type == descriptor.TYPE_MESSAGE:
            parsing_function = _read_protobuf_message
        elif descriptor.type == descriptor.TYPE_ENUM:

            def parsing_function(value):
                return descriptor.enum_type.values_by_number[value].name

        else:

            def parsing_function(value):
                return value

        # Then parse it
        if descriptor.label == descriptor.LABEL_REPEATED:
            parsed_value = [parsing_function(v) for v in value]
        else:
            parsed_value = parsing_function(value)

        d[descriptor.name] = parsed_value
    return d


def transform_to_transiter_structure(data, timezone_str=None):
    """
    Transform GTFS Realtime data in JSON like format to Transiter models

    :param data: the data
    :param timezone_str: a string decribing the timezone
    :return: feed_time, trips, route_ids in the feed
    """
    transformer = _GtfsRealtimeToTransiterTransformer(data, timezone_str)
    return transformer.transform()


class _GtfsRealtimeToTransiterTransformer:
    def __init__(self, raw_data, timezone_str=None):
        self._raw_data = raw_data
        self._trip_id_to_raw_entities = {}
        self._trip_id_to_transformed_entity = {}
        self._trip_id_to_trip_model = {}
        self._transformed_metadata = {}
        self._feed_route_ids = set()
        self._feed_time = None
        self._timestamp_to_datetime_cache = {}
        if timezone_str is None:
            self._timezone = None
        else:
            self._timezone = pytz.timezone(timezone_str)

    def transform(self):
        self._transform_feed_metadata()
        self._group_trip_entities()
        self._transform_trip_base_data()
        self._transform_trip_stop_events()
        self._update_stop_event_indices()
        return (
            self._feed_time,
            self._feed_route_ids,
            list(self._trip_id_to_trip_model.values()),
        )

    def _transform_feed_metadata(self):
        self._feed_time = self._timestamp_to_datetime(
            self._raw_data["header"]["timestamp"]
        )
        self._transformed_metadata = {"timestamp": self._feed_time}

    def _group_trip_entities(self):
        def attach_entity(entity_key, entity):
            trip_descriptor = entity.get("trip", {})
            trip_id = trip_descriptor.get("trip_id", None)
            if trip_id is None:
                return
            self._trip_id_to_raw_entities.setdefault(trip_id, {})
            self._trip_id_to_raw_entities[trip_id]["trip"] = trip_descriptor
            self._trip_id_to_raw_entities[trip_id][entity_key] = entity

        for main_entity in self._raw_data.get("entity", []):
            if "trip_update" in main_entity:
                attach_entity("trip_update", main_entity["trip_update"])
            if "vehicle" in main_entity:
                attach_entity("vehicle", main_entity["vehicle"])

    def _transform_trip_base_data(self):
        for trip_id, entity in self._trip_id_to_raw_entities.items():
            trip_data = entity.get("trip", {})

            trip = models.Trip()
            trip.id = trip_id
            trip.route_id = trip_data.get("route_id", None)
            trip.direction_id = trip_data.get("direction_id", None)
            start_date_str = trip_data.get("start_date", None)
            if start_date_str is not None:
                start_dt = datetime.datetime(
                    year=int(start_date_str[0:4]),
                    month=int(start_date_str[4:6]),
                    day=int(start_date_str[6:8]),
                )
                trip.start_time = self._localize_datetime(start_dt, naive=True)

            trip.vehicle_id = (
                entity.get("trip_update", {}).get("vehicle", {}).get("id", None)
            )

            vehicle_data = entity.get("vehicle", {})
            trip.last_update_time = self._timestamp_to_datetime(
                vehicle_data.get("timestamp", None)
            )
            if trip.last_update_time is None:
                trip.last_update_time = self._transformed_metadata.get(
                    "timestamp", None
                )
            raw_current_status = vehicle_data.get("current_status", None)
            if raw_current_status is not None:
                trip.current_status = trip.TripStatus[raw_current_status]
            trip.current_stop_sequence = vehicle_data.get("current_stop_sequence", 0)
            trip.current_stop_id = vehicle_data.get("stop_id", None)
            self._trip_id_to_trip_model[trip_id] = trip
            self._feed_route_ids.add(trip.route_id)

    def _transform_trip_stop_events(self):
        for trip_id, trip in self._trip_id_to_trip_model.items():
            entity = self._trip_id_to_raw_entities[trip_id]

            trip_update = entity.get("trip_update", {})
            stop_time_updates = []

            for stop_time_update_data in trip_update.get("stop_time_update", []):
                t = time.time()
                stop_time_update = models.TripStopTime()
                stop_time_update.stop_id = stop_time_update_data["stop_id"]
                stop_time_update.track = stop_time_update_data.get("track", None)
                stop_time_update.arrival_time = self._timestamp_to_datetime(
                    stop_time_update_data.get("arrival", {}).get("time", None)
                )
                stop_time_update.departure_time = self._timestamp_to_datetime(
                    stop_time_update_data.get("departure", {}).get("time", None)
                )
                stop_time_updates.append(stop_time_update)
            trip.stop_times = stop_time_updates

    def _update_stop_event_indices(self):
        for trip_id, trip in self._trip_id_to_trip_model.items():
            index = trip.current_stop_sequence
            for stop_time_update in trip.stop_times:
                stop_time_update.stop_sequence = index
                index += 1

    def _timestamp_to_datetime(self, timestamp):
        if timestamp is None or timestamp == 0:
            return None
        if timestamp not in self._timestamp_to_datetime_cache:
            utc_dt_naive = datetime.datetime.utcfromtimestamp(timestamp)
            utc_dt = pytz.UTC.localize(utc_dt_naive)
            self._timestamp_to_datetime_cache[timestamp] = self._localize_datetime(
                utc_dt
            )
        return self._timestamp_to_datetime_cache[timestamp]

    def _localize_datetime(self, dt, naive=False):
        if self._timezone is None:
            return dt
        if naive:
            return self._timezone.localize(dt)
        else:
            return dt.astimezone(self._timezone)
