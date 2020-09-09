"""
The GTFS Realtime Util contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/realtime/v2/
"""
import collections
import dataclasses
import datetime
import sys
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
        yield from parse_trips(self._gtfs_feed_message)

    def get_vehicles(self) -> typing.Iterable[parse.Vehicle]:
        yield from parse_vehicles(self._gtfs_feed_message)

    @classmethod
    def preview(cls, file_path):
        """
        Prints the contents of the GTFS Realtime protobuf file given at file_path.


        """
        with open(file_path, "rb") as f:
            content = f.read()
        parser = cls()
        parser.load_content(content)
        print(parser._gtfs_feed_message)


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


def parse_trips(feed_message):
    for entity in feed_message.entity:
        if not entity.HasField("trip_update"):
            continue
        trip_update = entity.trip_update
        trip_desc = trip_update.trip

        if trip_desc.HasField("start_time"):
            if trip_desc.HasField("start_date"):
                start_date_string = trip_desc.start_date
                base = datetime.datetime(
                    year=int(start_date_string[:4]),
                    month=int(start_date_string[4:6]),
                    day=int(start_date_string[6:8]),
                )
            else:
                # TODO: this is a buggy: the server's current day may not be equal to
                #  the day in the region of the transit system
                base = datetime.datetime.now()
            start_time_string = trip_desc.start_time
            trip_start_time = base.replace(
                hour=int(start_time_string[:2]),
                minute=int(start_time_string[3:5]),
                second=int(start_time_string[6:8]),
                microsecond=0,
            )
        else:
            trip_start_time = None

        yield parse.Trip(
            id=trip_desc.trip_id,
            route_id=_get_nullable_field(trip_desc, "route_id"),
            direction_id=_get_nullable_field(trip_desc, "direction_id"),
            schedule_relationship=parse.Trip.ScheduleRelationship(
                trip_desc.schedule_relationship
            )
            if trip_desc.HasField("schedule_relationship")
            else parse.Trip.ScheduleRelationship.UNKNOWN,
            start_time=trip_start_time,
            updated_at=_timestamp_to_datetime(trip_update.timestamp),
            delay=_get_nullable_field(trip_update, "delay"),
            stop_times=[
                _build_stop_time(stop_time_update)
                for stop_time_update in trip_update.stop_time_update
            ],
        )


def _build_stop_time(stop_time_update):
    # This the only way to actually get the extension...of course, the API can't
    # be trusted to not change but probably it won't.
    # noinspection PyProtectedMember
    extension_key = stop_time_update._extensions_by_number.get(TRANSITER_EXTENSION_ID)
    if extension_key is None:
        track = None
    else:
        track = _get_nullable_field(stop_time_update.Extensions[extension_key], "track")
    return parse.TripStopTime(
        stop_sequence=_get_nullable_field(stop_time_update, "stop_sequence"),
        stop_id=stop_time_update.stop_id,
        schedule_relationship=parse.TripStopTime.ScheduleRelationship(
            stop_time_update.schedule_relationship
        ),
        arrival_time=_timestamp_to_datetime(stop_time_update.arrival.time),
        arrival_delay=_get_nullable_field(stop_time_update.arrival, "delay"),
        arrival_uncertainty=_get_nullable_field(
            stop_time_update.arrival, "uncertainty"
        ),
        departure_time=_timestamp_to_datetime(stop_time_update.departure.time),
        departure_delay=_get_nullable_field(stop_time_update.departure, "delay"),
        departure_uncertainty=_get_nullable_field(
            stop_time_update.departure, "uncertainty"
        ),
        track=track,
    )


def _get_nullable_field(entity, field_name, default=None):
    if not entity.HasField(field_name):
        return default
    return getattr(entity, field_name)


@dataclasses.dataclass(unsafe_hash=True)
class _TripVehicleLink:
    trip_id: str
    vehicle_id: str


def parse_vehicles(feed_message):
    all_trips_ids = set()
    all_vehicle_ids = set()
    all_links = set()

    trip_id_to_descriptors = collections.defaultdict(list)
    trip_id_to_position = {}

    vehicle_id_to_descriptors = collections.defaultdict(list)
    vehicle_id_to_position = {}

    for entity in feed_message.entity:
        for sub_entity_key in ("vehicle", "trip_update"):
            if not entity.HasField(sub_entity_key):
                continue
            sub_entity = getattr(entity, sub_entity_key)

            trip_id = None
            vehicle_id = None
            if sub_entity.HasField("vehicle") and sub_entity.vehicle.HasField("id"):
                vehicle_id = sub_entity.vehicle.id
                all_vehicle_ids.add(vehicle_id)
            if sub_entity.HasField("trip") and sub_entity.trip.HasField("trip_id"):
                trip_id = sub_entity.trip.trip_id
                all_trips_ids.add(trip_id)

            if trip_id is None and vehicle_id is None:
                continue
            if trip_id is not None and vehicle_id is not None:
                all_links.add(_TripVehicleLink(trip_id=trip_id, vehicle_id=vehicle_id))

            if sub_entity.HasField("vehicle"):
                if trip_id is not None:
                    trip_id_to_descriptors[trip_id].append(sub_entity.vehicle)
                if vehicle_id is not None:
                    vehicle_id_to_descriptors[vehicle_id].append(sub_entity.vehicle)
            if sub_entity_key == "vehicle":
                if trip_id is not None:
                    trip_id_to_position[trip_id] = sub_entity
                if vehicle_id is not None:
                    vehicle_id_to_position[vehicle_id] = sub_entity

    for trip_id, vehicle_id in _trip_id_vehicle_id_tuples(
        all_trips_ids, all_vehicle_ids, all_links
    ):
        descriptors = (
            trip_id_to_descriptors[trip_id] + vehicle_id_to_descriptors[vehicle_id]
        )
        vehicle_position = vehicle_id_to_position.get(vehicle_id)
        if vehicle_position is None:
            vehicle_position = trip_id_to_position.get(trip_id)
        if len(descriptors) == 0 and vehicle_position is None:
            continue
        yield _build_vehicle(vehicle_id, trip_id, descriptors, vehicle_position)


def _trip_id_vehicle_id_tuples(all_trip_ids, all_vehicle_ids, all_links):
    trip_id_to_links = collections.defaultdict(set)
    vehicle_id_to_links = collections.defaultdict(set)
    for link in all_links:
        trip_id_to_links[link.trip_id].add(link)
        vehicle_id_to_links[link.vehicle_id].add(link)

    for trip_id in all_trip_ids:
        links = trip_id_to_links[trip_id]
        if len(links) == 1:
            vehicle_id = links.pop().vehicle_id
            if len(vehicle_id_to_links[vehicle_id]) > 1:
                continue
            yield trip_id, vehicle_id
        elif len(links) == 0:
            yield trip_id, None
        else:
            # Skip trips with more than one vehicle
            pass

    for vehicle_id in all_vehicle_ids:
        if vehicle_id in vehicle_id_to_links:
            continue
        yield None, vehicle_id


def _build_vehicle(vehicle_id, trip_id, descriptors, vehicle_position):
    vehicle = parse.Vehicle(id=vehicle_id, trip_id=trip_id)
    for vehicle_desc in descriptors:
        if vehicle_desc.HasField("label"):
            vehicle.label = vehicle_desc.label
        if vehicle_desc.HasField("license_plate"):
            vehicle.license_plate = vehicle_desc.license_plate

    if vehicle_position is not None:
        for field_name in ["latitude", "longitude", "bearing", "odometer", "speed"]:
            setattr(
                vehicle,
                field_name,
                _get_nullable_field(vehicle_position.position, field_name),
            )
        vehicle.current_stop_sequence = _get_nullable_field(
            vehicle_position, "current_stop_sequence"
        )
        vehicle.current_stop_id = _get_nullable_field(vehicle_position, "stop_id")
        vehicle.current_status = parse.Vehicle.Status(vehicle_position.current_status)
        vehicle.congestion_level = parse.Vehicle.CongestionLevel(
            vehicle_position.congestion_level
        )
        if vehicle_position.HasField("occupancy_status"):
            vehicle.occupancy_status = parse.Vehicle.OccupancyStatus(
                vehicle_position.occupancy_status
            )
    return vehicle


class _VehicleIdentifier:
    vehicle_id: str = None
    trip_id: str = None

    def is_valid(self):
        return self.vehicle_id is not None or self.trip_id is not None

    def __hash__(self):
        if self.vehicle_id is not None:
            return hash((self.vehicle_id, None))
        return hash((None, self.trip_id))

    def __eq__(self, other):
        if self.vehicle_id is not None:
            return self.vehicle_id == other.vehicle_id
        return self.trip_id == other.trip_id

    def __repr__(self):
        return f"({self.vehicle_id}, {self.trip_id})"


if __name__ == "__main__":
    # python -m transiter.parse.gtfsrealtime path/to/gtfs.rt
    GtfsRealtimeParser.preview(sys.argv[1])
