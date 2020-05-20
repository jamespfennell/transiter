"""
The GTFS Realtime Util contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/realtime/v2/
"""
import collections
import datetime
import typing

import pytz

from transiter.parse import transiter_gtfs_rt_pb2
from transiter.parse import types as parse
from transiter.parse.parser import TransiterParser


class GtfsRealtimeParser(TransiterParser):

    GTFS_REALTIME_PB2_MODULE = None

    _gtfs_feed_message = None

    def load_content(self, content: bytes) -> None:
        if self.GTFS_REALTIME_PB2_MODULE is not None:
            pb2_module = self.GTFS_REALTIME_PB2_MODULE
        else:
            pb2_module = transiter_gtfs_rt_pb2
        self._gtfs_feed_message = pb2_module.FeedMessage()
        self._gtfs_feed_message.ParseFromString(content)
        self.post_process_feed_message(self._gtfs_feed_message)

    @staticmethod
    def post_process_feed_message(feed_message):
        pass

    def get_timestamp(self) -> typing.Optional[datetime.datetime]:
        return _timestamp_to_datetime(self._gtfs_feed_message.header.timestamp)

    def get_alerts(self) -> typing.Iterable[parse.Alert]:
        yield from parse_alerts(self._gtfs_feed_message)

    def get_trips(self) -> typing.Iterable[parse.Trip]:
        (feed_time, trips) = transform_to_transiter_structure(
            _read_protobuf_message(self._gtfs_feed_message), "America/New_York"
        )
        return trips


# Smallest number that is expressible as the sum of two cubes in two different ways.
TRANSITER_EXTENSION_ID = 1729  # = 1^3 + 12^3 = 9^3 + 10^3


def parse_alerts(feed_message):
    for entity in feed_message.entity:
        if not entity.HasField("alert"):
            continue
        alert_id = entity.id
        alert = entity.alert
        active_periods = [
            parse.AlertActivePeriod(
                starts_at=_timestamp_to_datetime(active_period.start),
                ends_at=_timestamp_to_datetime(active_period.end),
            )
            for active_period in alert.active_period
        ]
        parsed_alert = parse.Alert(
            id=alert_id,
            cause=parse.Alert.Cause(alert.cause),
            effect=parse.Alert.Effect(alert.effect),
            messages=list(build_alert_messages(alert)),
            active_periods=active_periods,
        )
        attach_informed_entities(alert, parsed_alert)
        attach_transiter_extension_data(alert, parsed_alert)
        yield parsed_alert


def attach_transiter_extension_data(alert, parsed_alert: parse.Alert):
    # This the only way to actually get the extension...of course, the API can't
    # be trusted to not change but probably it won't.
    # noinspection PyProtectedMember
    extension_key = alert._extensions_by_number.get(TRANSITER_EXTENSION_ID)
    if extension_key is None:
        return
    additional_data = alert.Extensions[extension_key]
    parsed_alert.created_at = _timestamp_to_datetime(additional_data.created_at)
    parsed_alert.updated_at = _timestamp_to_datetime(additional_data.updated_at)
    if additional_data.HasField("sort_order"):
        parsed_alert.sort_order = additional_data.sort_order


def _timestamp_to_datetime(timestamp):
    if timestamp == 0 or timestamp is None:
        return None
    return datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.UTC)


def attach_informed_entities(alert, parsed_alert: parse.Alert):
    for informed_entity in alert.informed_entity:
        if informed_entity.HasField("trip"):
            if informed_entity.trip.HasField("trip_id"):
                parsed_alert.trip_ids.append(informed_entity.trip.trip_id)
                continue
            elif informed_entity.trip.HasField("route_id"):
                parsed_alert.route_ids.append(informed_entity.trip.route_id)
        elif informed_entity.HasField("route_id"):
            parsed_alert.route_ids.append(informed_entity.route_id)
        elif informed_entity.HasField("stop_id"):
            parsed_alert.stop_ids.append(informed_entity.stop_id)
        elif informed_entity.HasField("agency_id"):
            parsed_alert.agency_ids.append(informed_entity.agency_id)


def build_alert_messages(alert):
    def get_language(translated_string):
        if translated_string.HasField("language"):
            return translated_string.language
        return None

    language_to_message = collections.defaultdict(
        lambda: parse.AlertMessage(header="", description="")
    )
    for header in alert.header_text.translation:
        language_to_message[get_language(header)].header = header.text
    for description in alert.description_text.translation:
        language_to_message[get_language(description)].description = description.text
    for url in alert.url.translation:
        language_to_message[get_language(url)].url = url.text
    for language, message in language_to_message.items():
        message.language = language
        yield message


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
        return (self._feed_time, list(self._trip_id_to_trip_model.values()))

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
            vehicle_data = entity.get("vehicle", {})

            start_date_str = trip_data.get("start_date", None)
            if start_date_str is not None:
                start_dt = datetime.datetime(
                    year=int(start_date_str[0:4]),
                    month=int(start_date_str[4:6]),
                    day=int(start_date_str[6:8]),
                )
                trip_start_time = self._localize_datetime(start_dt, naive=True)
            else:
                trip_start_time = None

            raw_current_status = vehicle_data.get("current_status", None)
            if raw_current_status is not None:
                current_status = parse.Trip.Status[raw_current_status]
            else:
                current_status = None

            trip = parse.Trip(
                id=trip_id,
                route_id=trip_data.get("route_id", None),
                direction_id=trip_data.get("direction_id", None),
                start_time=trip_start_time,
                train_id=entity.get("trip_update", {})
                .get("vehicle", {})
                .get("id", None),
                updated_at=self._timestamp_to_datetime(
                    vehicle_data.get("timestamp", None)
                ),
                current_status=current_status,
                current_stop_sequence=vehicle_data.get("current_stop_sequence", 0),
                current_stop_id=vehicle_data.get("stop_id", None),
            )
            self._trip_id_to_trip_model[trip_id] = trip

    def _transform_trip_stop_events(self):
        for trip_id, trip in self._trip_id_to_trip_model.items():
            entity = self._trip_id_to_raw_entities[trip_id]

            trip_update = entity.get("trip_update", {})
            stop_time_updates = []

            for stop_time_update_data in trip_update.get("stop_time_update", []):
                stop_time_update = parse.TripStopTime(
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
