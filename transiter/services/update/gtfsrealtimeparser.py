"""
The GTFS Realtime Util contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/realtime/v2/
"""
import datetime

import pytz
from google.transit import gtfs_realtime_pb2

from transiter import models


def create_parser(gtfs_realtime_pb2_module=None, post_pb2_parsing_function=None):
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

    :param gtfs_realtime_pb2_module: optional, the protobuffers module to use
        to read the feed. Defaults to the official module on PyPI.
    :param post_pb2_parsing_function: the function described in (2). It takes
        a single argument, which is the JSON data structure. It returns nothing;
        rather, it alterts the JSON structure in place.
    :return: the parser
    """
    # Additional arguments are accepted for forwards compatibility
    # noinspection PyUnusedLocal
    def parser(binary_content, *args, **kwargs):
        gtfs_data = read_gtfs_realtime(binary_content, gtfs_realtime_pb2_module)
        # print(json.dumps(gtfs_data))
        if post_pb2_parsing_function is not None:
            post_pb2_parsing_function(gtfs_data)
        (feed_time, trips) = transform_to_transiter_structure(
            gtfs_data, "America/New_York"
        )
        return trips

    return parser


built_in_parser = create_parser()


def read_gtfs_realtime(content, gtfs_realtime_pb2_module=None):
    """
    Convert a binary GTFS Realtime feed to a JSON-like data structure

    :param content: GTFS realtime binary data
    :param gtfs_realtime_pb2_module: GTFS realtime module
    :return: the data in a JSON-like data structure
    """
    if gtfs_realtime_pb2_module is None:
        gtfs_realtime_pb2_module = gtfs_realtime_pb2

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


ACTIVE_PERIOD = "active_period"
AGENCY_ID = "agency_id"
ALERT = "alert"
CAUSE = "cause"
DESCRIPTION_TEXT = "description_text"
EFFECT = "effect"
END = "end"
ENTITY = "entity"
HEADER_TEXT = "header_text"
ID = "id"
INFORMED_ENTITY = "informed_entity"
ROUTE_ID = "route_id"
START = "start"
TRANSLATION = "translation"
TEXT = "text"
URL = "url"


class _GtfsRealtimeToTransiterTransformer:
    def __init__(self, raw_data, timezone_str=None):
        self._raw_data = raw_data
        self._trip_id_to_raw_entities = {}
        self._trip_id_to_transformed_entity = {}
        self._trip_id_to_trip_model = {}
        self._transformed_metadata = {}
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
            list(self._trip_id_to_trip_model.values())
            + self.build_alerts(self._raw_data),
        )

    def build_alerts(self, raw_data):
        def get_text(alert_data_, key):
            texts = alert_data_.get(key, {}).get(TRANSLATION, [])
            if len(texts) == 0:
                return None
            return texts[0][TEXT]

        def get_enum_value(enum, key, default):
            try:
                return enum[key]
            except KeyError:
                return default

        alerts = []
        for entity in raw_data.get(ENTITY, []):
            alert_id = entity.get(ID)
            alert_data = entity.get(ALERT)
            if alert_id is None or alert_data is None:
                continue
            alert = models.Alert(
                id=alert_id,
                cause=get_enum_value(
                    models.Alert.Cause,
                    alert_data.get(CAUSE),
                    models.Alert.Cause.UNKNOWN_CAUSE,
                ),
                effect=get_enum_value(
                    models.Alert.Effect,
                    alert_data.get(EFFECT),
                    models.Alert.Effect.UNKNOWN_EFFECT,
                ),
                header=get_text(alert_data, HEADER_TEXT),
                description=get_text(alert_data, DESCRIPTION_TEXT),
                url=get_text(alert_data, URL),
                start_time=self._timestamp_to_datetime(
                    alert_data.get(ACTIVE_PERIOD, {}).get(START)
                ),
                end_time=self._timestamp_to_datetime(
                    alert_data.get(ACTIVE_PERIOD, {}).get(START)
                ),
            )
            informed_entities = alert_data.get(INFORMED_ENTITY, {})
            alert.agency_ids = [
                informed_entity[AGENCY_ID]
                for informed_entity in informed_entities
                if AGENCY_ID in informed_entity
            ]
            alert.route_ids = [
                informed_entity[ROUTE_ID]
                for informed_entity in informed_entities
                if ROUTE_ID in informed_entity
            ]
            alerts.append(alert)
        return alerts

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
            # if "alert" in main_entity:
            #    self._alerts_raw_data.append(main_entity["alert"])

    def _transform_trip_base_data(self):
        for trip_id, entity in self._trip_id_to_raw_entities.items():
            trip_data = entity.get("trip", {})

            trip = models.TripLight()
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
                trip.current_status = models.Trip.TripStatus[raw_current_status]
            trip.current_stop_sequence = vehicle_data.get("current_stop_sequence", 0)
            trip.current_stop_id = vehicle_data.get("stop_id", None)
            self._trip_id_to_trip_model[trip_id] = trip

    def _transform_trip_stop_events(self):
        for trip_id, trip in self._trip_id_to_trip_model.items():
            entity = self._trip_id_to_raw_entities[trip_id]

            trip_update = entity.get("trip_update", {})
            stop_time_updates = []

            for stop_time_update_data in trip_update.get("stop_time_update", []):
                stop_time_update = models.TripStopTime.from_feed(
                    trip_id=trip_id,
                    stop_id=stop_time_update_data["stop_id"],
                    arrival_time=self._timestamp_to_datetime(
                        stop_time_update_data.get("arrival", {}).get("time", None)
                    ),
                    arrival_delay=stop_time_update_data.get("arrival", {}).get("delay"),
                    arrival_uncertainty=stop_time_update_data.get("arrival", {}).get(
                        "uncertainty"
                    ),
                    departure_time=self._timestamp_to_datetime(
                        stop_time_update_data.get("departure", {}).get("time", None)
                    ),
                    departure_delay=stop_time_update_data.get("departure", {}).get(
                        "delay"
                    ),
                    departure_uncertainty=stop_time_update_data.get(
                        "departure", {}
                    ).get("uncertainty"),
                    track=stop_time_update_data.get("track", None),
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


class TripDataCleaner:
    """
    The TripDataCleaner provides a mechanism for cleaning valid and removing
    invalid Trips and TripStopTimes.

    To use the TripDataCleaner, you must provide a number of cleaning functions.
    Trip cleaning functions accept two arguments - the current FeedUpdate
    and the Trip being cleaned,
    and perform some operations to clean up the trip - for example, switching
    the direction of Trips in a given route to compensate for a known bug in a
    Transit agency's data feed. If the cleaner returns
    False, then that Trip is removed from the collection. TripStopTime cleaners
    work identically.

    After initializing the cleaner with cleaning functions, a list of Trips
    is passed into its clean method. The cleaners operate on all of the Trips
    and their contained TripStopTimes, remove entities based on cleaner function
    results, and returns the list of cleaned trips.
    """

    def __init__(self, trip_cleaners, stop_time_cleaners):
        """
        Initialize a new TripDataCleaner

        :param trip_cleaners: list of Trip cleaning functions
        :param stop_time_cleaners: list of TripStopTime cleaning functions
        """
        self._trip_cleaners = trip_cleaners
        self._stop_time_cleaners = stop_time_cleaners

    def clean(self, trips):
        """
        Clean a collection of trips.

        :param trips: the trips to clean
        :return: the cleaned trips with bad trips removed
        """
        trips_to_keep = []
        for trip in trips:
            if not isinstance(trip, models.Trip):
                trips_to_keep.append(trip)
                continue
            result = True
            for trip_cleaner in self._trip_cleaners:
                result = trip_cleaner(trip)
                if not result:
                    break
            if not result:
                continue

            for stop_time_update in trip.stop_times:
                for stop_time_cleaner in self._stop_time_cleaners:
                    stop_time_cleaner(stop_time_update)

            trips_to_keep.append(trip)

        return trips_to_keep
