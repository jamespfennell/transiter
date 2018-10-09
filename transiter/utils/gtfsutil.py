import datetime
import importlib
from google.transit import gtfs_realtime_pb2
from google.protobuf.message import DecodeError


class GtfsRealtimeExtension():

    def __init__(self, pb_module, base_module):
        self._pb_module = pb_module
        self._base_module = base_module

    def activate(self):
        importlib.import_module(self._pb_module, self._base_module)


# Rename pb2_to_json
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
    except DecodeError:
        return {}
    return _parse_protobuf_message(gtfs_feed)


def _identity(value):
    return value


# Takes 40 milliseconds for the 123456 -> kind of a small bottleneck
# Can it be sped up?
def _parse_protobuf_message(message):
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
            parsing_function = _parse_protobuf_message
        elif descriptor.type == descriptor.TYPE_ENUM:
            parsing_function = (lambda index:
                descriptor.enum_type.values_by_number[index].name)
        else:
            parsing_function = _identity

        # Then parse it
        if descriptor.label == descriptor.LABEL_REPEATED:
            parsed_value = [parsing_function(v) for v in value]
        else:
            parsed_value = parsing_function(value)

        d[descriptor.name] = parsed_value
    return d


def transform_to_transiter_structure(content):

    data = content
    try:
        header = data['header']
    except KeyError:
        return {}
    actual_feed_route_ids = set()

    # Now iterate over trips in the feed, placing the trip data in memory
    # Each trip corresponds to two different entities in the feed file: a
    # trip_update entity and a vehicle entity
    # (the latter provided only if the trip has been assigned). Both entities
    # contain basic trip information in a
    # trip field.
    trips = {}
    vehicle_parsed_trip_ids = set()
    trip_update_parsed_trip_ids = set()
    for entity in data['entity']:
        # Based on which type of entity, the location of the trip data is different.
        if 'trip_update' in entity:
            trip = entity['trip_update']['trip']
        elif 'vehicle' in entity:
            trip = entity['vehicle']['trip']
        else:
            continue

        actual_feed_route_ids.add(trip['route_id'])

        # Now generate the trip_uid and the start time
        try:
            trip_id = trip['trip_id']
        except Exception as e:
            # Should log something here and skip
            continue

        # If the basic trip_uid settings have already been imported, do nothing;
        # otherwise, import then.
        if trip_id in trips:
            trip_data = trips[trip_id]
        else:
            trip_data = {
                'trip_id' : trip_id,
                'route_id' : trip['route_id'],
                'start_date': trip['start_date'],
                'current_status': None,
                'current_stop_sequence': 0,
                'last_update_time': None,
                'feed_update_time': _timestamp_to_datetime(header['timestamp'])
            }
            trips[trip_id] = trip_data

        # TODO: take this logic out of here and put in gtfsupdater
        # What is this actually doing?
        if "nyct_trip_descriptor" in trip:
            trip_data.update(trip["nyct_trip_descriptor"])

        if 'vehicle' in entity:
            update_time = _timestamp_to_datetime(entity['vehicle']['timestamp'])
            trip_data.update({
                'last_update_time' : update_time,
                'current_status': entity['vehicle']['current_status'],
                'current_stop_sequence': entity['vehicle']['current_stop_sequence']
            })
            vehicle_parsed_trip_ids.add(trip_id)

        if 'trip_update' in entity:
            trip_data['stop_events'] = []
            for stop_time_update in entity['trip_update']['stop_time_update']:
                stop_event_data = {
                    'stop_id' : stop_time_update['stop_id'],
                    'track': stop_time_update.get('track', None)
                }

                # Arrival/departure time information
                # TODO Replace these by get(key, default) <- could use this for gtfs
                if 'arrival' in stop_time_update and stop_time_update['arrival']['time'] != 0:
                    stop_event_data['arrival_time'] = _timestamp_to_datetime(stop_time_update['arrival']['time'])
                else:
                    stop_event_data['arrival_time'] = None
                if 'departure' in stop_time_update and stop_time_update['departure']['time'] != 0:
                    stop_event_data['departure_time'] = _timestamp_to_datetime(stop_time_update['departure']['time'])
                else:
                    stop_event_data['departure_time'] = None

                trip_data['stop_events'].append(stop_event_data)

                # TODO: take this logic out of here
                if "nyct_stop_time_update" in stop_time_update:
                    try:
                        mta_data = stop_time_update["nyct_stop_time_update"]
                        if 'actual_track' not in mta_data:
                            stop_event_data['track'] = mta_data['scheduled_track']
                        else:
                            stop_event_data['track'] = mta_data['actual_track']
                    except KeyError:
                        print(mta_data)
                        print('Bug')
                else:
                    stop_event_data['track'] = None

            trip_update_parsed_trip_ids.add(trip_id)

        # This following condition checks that both the vehicle and trip_update
        # entities respectively have been imported.
        # If they have been, the sequence indices should be updated to factor
        # in the number of stops already passed
        # (which is given by the current_stop_sequence field in the vehicle entity
        if trip_id in trip_update_parsed_trip_ids and trip_id in vehicle_parsed_trip_ids:
            current_stop_sequence = trip_data['current_stop_sequence']
            for stop_event_data in trip_data['stop_events']:
                current_stop_sequence += 1
                stop_event_data['sequence_index'] = current_stop_sequence

    return {
        'timestamp': _timestamp_to_datetime(header['timestamp']),
        'route_ids': list(actual_feed_route_ids),
        'trips': list(trips.values())
    }


def _timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)



