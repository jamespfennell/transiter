import datetime
import importlib
import time
from google.transit import gtfs_realtime_pb2
from google.protobuf.message import DecodeError
from transiter import models
import pytz


class GtfsRealtimeExtension:

    def __init__(self, pb_module, base_module):
        self._pb_module = pb_module
        self._base_module = base_module

    def activate(self):
        importlib.import_module(self._pb_module, self._base_module)


# TODO Rename pb2_to_json
def read_gtfs_realtime(content, extension=None):
    """
    Convert a binary GTFS Realtime feed from protobuf format to a JSON-like
    data structure
    :param content: GTFS realtime binary data
    :param extension: an optional GtfsRealtimeExtension object
    :return: the data in a JSON-like dictionary and list structure
    """
    if extension is not None:
        extension.activate()
    gtfs_feed = gtfs_realtime_pb2.FeedMessage()
    try:
        gtfs_feed.ParseFromString(content)
    except DecodeError as e:
        # TODO: make this a more specific (feed) service exception
        raise Exception(e)
    return _read_protobuf_message(gtfs_feed)


# Takes 40 milliseconds for the 123456 -> kind of a small bottleneck
# Can it be sped up?
def _read_protobuf_message(message):
    """
    Convert a protobuf message into a dictionary and list structure.
    This is not an exaustive converter but mean to be sufficient for GTFS
    realtime
    :param message: a google.protobuf.message.Message
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
    transformer = _GtfsRealtimeToTransiterTransformer(data, timezone_str)
    return transformer.transform()


class _GtfsRealtimeToTransiterTransformer:

    def __init__(self, raw_data, timezone_str=None):
        self._raw_data = raw_data
        self._trip_id_to_raw_entities = {}
        self._trip_id_to_transformed_entity = {}
        self._trip_id_to_trip_model = {}
        self._transformed_metadata = None
        self._feed_route_ids = set()
        self._feed_time = None
        if timezone_str is None:
            self._timezone = None
        else:
            # Todo: what if this doesn't work?
            self._timezone = pytz.timezone(timezone_str)

    def transform(self):
        self._transform_feed_metadata()
        self._group_trip_entities()
        self._transform_trip_base_data()
        self._transform_trip_stop_events()
        self._update_stop_event_indices()
        return (self._feed_time,
                self._feed_route_ids,
                list(self._trip_id_to_trip_model.values()))

    def _transform_feed_metadata(self):
        self._feed_time = self._timestamp_to_datetime(
            self._raw_data['header']['timestamp'])
        self._transformed_metadata = {
            'timestamp': self._feed_time
        }

    def _group_trip_entities(self):
        for entity in self._raw_data['entity']:
            main_entity_key = None
            if 'trip_update' in entity:
                main_entity_key = 'trip_update'
            elif 'vehicle' in entity:
                main_entity_key = 'vehicle'
            if main_entity_key is None:
                continue
            trip_entity = entity.get(main_entity_key, {}).get('trip', {})
            trip_id = trip_entity.get('trip_id', None)
            if trip_id is None:
                continue
            self._trip_id_to_raw_entities.setdefault(trip_id, {})
            self._trip_id_to_raw_entities[trip_id]['trip'] = trip_entity
            self._trip_id_to_raw_entities[trip_id][main_entity_key] \
                = entity[main_entity_key]

    def _transform_trip_base_data(self):
        for trip_id, entity in self._trip_id_to_raw_entities.items():
            trip_data = entity.get('trip', {})

            trip = models.Trip()
            trip.id = trip_id
            trip.route_id = trip_data.get('route_id', None)
            trip.direction_id = trip_data.get('direction_id', None)
            start_date_str = trip_data.get('start_date', None)
            if start_date_str is not None:
                start_dt = datetime.datetime(
                    year=int(start_date_str[0:4]),
                    month=int(start_date_str[4:6]),
                    day=int(start_date_str[6:8]))
                trip.start_time = self._localize_datetime(start_dt)
            # TODO should be vehicle_id and go in the vehicle section
            trip.train_id = trip_data.get('train_id', None)

            vehicle_data = entity.get('vehicle', {})
            trip.last_update_time = self._timestamp_to_datetime(
                vehicle_data.get('timestamp', None))
            trip.current_status = vehicle_data.get('current_status', None)
            trip.current_stop_sequence = vehicle_data.get('current_stop_sequence', 0)
            self._trip_id_to_trip_model[trip_id] = trip
            self._feed_route_ids.add(trip.route_id)

            trip_data = self._trip_id_to_transformed_entity.get(trip_id, {})
            trip = entity['trip']
            trip_data.update({
                'id': trip_id,
                'route_id': trip['route_id'],
                'start_date': trip.get('start_date', None),
                'train_id': trip.get('train_id', None),
                'direction_id': trip.get('direction_id', None),
                'current_status': trip.get('status', None),
                'current_stop_sequence': 0,
                'last_update_time': None,
                'feed_update_time': self._feed_time
            })
            self._feed_route_ids.add(trip['route_id'])
            if 'vehicle' in entity:
                vehicle = entity['vehicle']
                update_time = self._timestamp_to_datetime(vehicle['timestamp'])
                trip_data.update({
                    'last_update_time': update_time,
                    'current_status': vehicle.get(
                        'current_status', trip_data['current_status']),
                    'current_stop_sequence': vehicle.get(
                        'current_stop_sequence', trip_data['current_stop_sequence'])
                })
            self._trip_id_to_transformed_entity[trip_id] = trip_data

    def _transform_trip_stop_events(self):
        for trip_id, trip in self._trip_id_to_trip_model.items():
            entity = self._trip_id_to_raw_entities[trip_id]

            trip_update = entity.get('trip_update', None)
            trip_data = self._trip_id_to_transformed_entity.get(trip_id, {})
            trip_data['stop_events'] = []
            trip.stop_events = []



            if trip_update is None:
                self._trip_id_to_transformed_entity[trip_id] = trip_data
                continue
            for stop_time_update_data in trip_update['stop_time_update']:
                stop_time_update = models.StopTimeUpdate()
                stop_time_update.stop_id = stop_time_update_data['stop_id']
                stop_time_update.track = stop_time_update_data.get('track', None)
                stop_time_update.arrival_time = (
                    self._timestamp_to_datetime(
                        stop_time_update_data.get('arrival', {}).get('time', None)))
                stop_time_update.departure_time = self._timestamp_to_datetime(
                    stop_time_update_data.get('departure', {}).get('time', None))
                trip.stop_events.append(stop_time_update)

                stop_event_data = {
                    'stop_id': stop_time_update_data['stop_id'],
                    'track': stop_time_update_data.get('track', None),
                    'arrival_time': None,
                    'departure_time': None
                }
                for time_type in ('arrival', 'departure'):
                    time_entity = stop_time_update_data.get(time_type, None)
                    if time_entity is None:
                        continue
                    timestamp = time_entity.get('time', 0)
                    stop_event_data[time_type + '_time'] =\
                        self._timestamp_to_datetime(timestamp)

                trip_data['stop_events'].append(stop_event_data)
            self._trip_id_to_transformed_entity[trip_id] = trip_data

    def _update_stop_event_indices(self):
        for trip_id, trip in self._trip_id_to_trip_model.items():
            entity = self._trip_id_to_transformed_entity[trip_id]
            index = entity['current_stop_sequence']
            for stop_event in entity['stop_events']:
                index += 1
                stop_event['stop_sequence'] = index
            index = trip.current_stop_sequence
            for stop_time_update in trip.stop_events:
                stop_time_update.stop_sequence = index
                index += 1

    def _collect_transformed_data(self):
        transformed_data = self._transformed_metadata
        transformed_data.update({
            'route_ids': list(self._feed_route_ids),
            'trips': list(self._trip_id_to_transformed_entity.values()),
        })
        return transformed_data

    def _timestamp_to_datetime(self, timestamp):
        if timestamp is None or timestamp == 0:
            return None
        return self._localize_datetime(
            datetime.datetime.fromtimestamp(timestamp))

    def _localize_datetime(self, dt):
        if self._timezone is None:
            return dt
        return self._timezone.localize(dt)