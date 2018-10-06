import importlib
#from .protobuf import gtfs_realtime_pb2
#from .protobuf import nyc_subway_pb2
from google.transit import gtfs_realtime_pb2
import json
import datetime
import time
from ..database import models
from ..database import syncutil
from ..database import connection
from ..utils import jsonutil

def jsonify(data):
    return json.dumps(data, indent=2, separators=(',', ': '), default=json_serial)
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, models.Base):
        return str(obj)
    raise TypeError ("Type %s not serializable" % type(obj))




class GtfsExtension():

    def __init__(self, pb_module, base_module):
        self._pb_module = pb_module
        self._base_module = base_module

    def activate(self):
        importlib.import_module(self._pb_module, self._base_module)



def restructure(content):

    data = content

    header = data['header']
    # Read header information from the feed: the time it was created, and the routes contained within.
    #feed_timestamp = header['timestamp']
    #if feed_timestamp == 0:
    #    print('Invalid feed, raw feed text:')
    #    print(gtfs_feed)
    #    raise InvalidGTFSFile('Invalid GTFS file.')
    #feed_time = timestamp_to_datetime(feed_timestamp)
    #feed_route_ids = set()
    actual_feed_route_ids = set()

    # Now iterate over trips in the feed, placing the trip data in memory
    # Each trip corresponds to two different entities in the feed file: a trip_update entity and a vehicle entity
    # (the latter provided only if the trip has been assigned). Both entities contain basic trip information in a
    # trip field.
    trips = {}
    for entity in data['entity']:
        # Based on which type of entity, the location of the trip data is different.
        if 'trip_update' in entity:
            trip = entity['trip_update']['trip']
        if 'vehicle' in entity:
            trip = entity['vehicle']['trip']

        actual_feed_route_ids.add(trip['route_id'])

        # Now generate the trip_uid and the start time
        try:
            trip_uid = trip['trip_id']
        except Exception as e:
            #print('Could not generate trip_uid; skipping.')
            #print(e)
            continue

        # If the basic trip_uid settings have already been imported, do nothing; otherwise, import then.
        if trip_uid in trips:
            trip_data = trips[trip_uid]
        else:
            trip_data = {
                    'trip_id' : trip_uid,
                    'route_id' : trip['route_id'],
                    'start_date': trip['start_date'],
                    'current_status': None,
                    'current_stop_sequence': 0,
                    'last_update_time': None,
                    'feed_update_time': timestamp_to_datetime(header['timestamp'])
                    }

            trips[trip_uid] = trip_data
        #print('Trip_uid')
        #print(trip_uid)
        # TODO: take this logic out of here
        if "nyct_trip_descriptor" in trip:
            trip_data.update(trip["nyct_trip_descriptor"])
        if 'vehicle' in entity:
            #current_stop_sequence = entity['vehicle']['current_stop_sequence']
            update_time = timestamp_to_datetime(entity['vehicle']['timestamp'])
            trip_data.update({
                'last_update_time' : update_time,
                'current_status': entity['vehicle']['current_status'],
                'current_stop_sequence': entity['vehicle']['current_stop_sequence']
            })



        if 'trip_update' in entity:
            trip_data['stop_events'] = []
            current_stop_sequence = 0
            for stop_time_update in entity['trip_update']['stop_time_update']:
                stop_event_data = {
                        'stop_id' : stop_time_update['stop_id'],
                        }

                # Arrival/departure time information
                # TODO Replace these by get(key, default) <- could use this for gtfs
                if 'arrival' in stop_time_update and +stop_time_update['arrival']['time'] != 0:
                    stop_event_data['arrival_time'] = timestamp_to_datetime(stop_time_update['arrival']['time'])
                else:
                    stop_event_data['arrival_time'] = None
                if 'departure' in stop_time_update and stop_time_update['departure']['time'] != 0:
                    stop_event_data['departure_time'] = timestamp_to_datetime(stop_time_update['departure']['time'])
                else:
                    stop_event_data['departure_time'] = None

                trip_data['stop_events'].append(stop_event_data)

                # TODO: take this logic out of here
                if "nyct_stop_time_update" in stop_time_update:
                    trip_data.update(stop_time_update["nyct_stop_time_update"])

        # This following condition checks that both the vehicle and trip_update entities respectively have been imported.
        # If they have been, the sequence indices should be updated to factor in the number of stops already passed
        # (which is given by the current_stop_sequence field in the vehicle entity
        if 'stop_events' in trip_data:
            # Update the stop sequence indices
            current_stop_sequence = trip_data['current_stop_sequence']
            for stop_event_data in trip_data['stop_events']:
                current_stop_sequence += 1
                stop_event_data['sequence_index'] = current_stop_sequence

        #trip_data['terminating_stop_uid'] = stop_event_data['stop_id']

    response = {
            'timestamp': timestamp_to_datetime(header['timestamp']),
            'route_ids': list(actual_feed_route_ids),
            'trips' : list(trips.values())
            }
    #print('Parsing complete.')
    return response



# Rename pb2_to_json
def gtfs_to_json(content, extension=None):
    #print('1.1 {}'.format(time.time()))
    if extension is not None:
        extension.activate()
    gtfs_feed = gtfs_realtime_pb2.FeedMessage()
    #print('1.2 {}'.format(time.time()))
    gtfs_feed.ParseFromString(content)
    #print('1.3 {}'.format(time.time()))
    a = _parse_protobuf_message(gtfs_feed)
    #print('1.4 {}'.format(time.time()))
    return a

def _identity(value):
    return value


# Takes 40 milliseconds for the 123456 -> kind of a small bottleneck
# Can it be sped up?
def _parse_protobuf_message(message):
    """
    Input is of type a google.protobuf.message.Message
    Returns a dictionary of {key: value}
    """
    d = {}
    for (descriptor, value) in message.ListFields():
        # if descriptor.type = 11, this is a message field
        # Recursively parse it with the function
        # Otherwise just return the value
        if descriptor.type == descriptor.TYPE_MESSAGE:
            parsing_function = _parse_protobuf_message
        elif descriptor.type == descriptor.TYPE_ENUM:
            parsing_function = (lambda index:
                descriptor.enum_type.values_by_number[index].name)
        else:
            parsing_function = _identity

        # If this is a repeated field
        if descriptor.label == descriptor.LABEL_REPEATED:
            parsed_value = [parsing_function(v) for v in value]
        else:
            parsed_value = parsing_function(value)

        d[descriptor.name] = parsed_value

    return d

def _parse_protobuf_enum(value):
    help(value)
    exit()
    return "enum"
    pass

import datetime
def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)


def archive_function_factory(cutoff):
    def archive_function(session, stop_event):
        #print(stop_event)
        if cutoff is not None and stop_event.sequence_index < cutoff:
            stop_event.future = False
        else:
            session.delete(stop_event)
    return archive_function

#to_timestamp(int)
# Should accept system as a parameter
# Should be inside the dbsync instead ...
# IN the dbsyncutil
# Call this sync_trip_data
# TODO need to also take in the transit system id as route_id is ambiguous
def sync_to_db(data):

    #print('Beginning the mega query')



    session = connection.get_session()

    # TODO: why do I have all() here?
    query = session.query(models.Route.route_id, models.Route.id) \
        .filter(models.Route.route_id.in_(data['route_ids']))\
        .all()
    route_id_to_route_pri_key = {route_id: route_pri_key for (route_id, route_pri_key) in query}

    # TODO Investigate breaking this up into two queries
    # Should be easy as can find the stop events using the trip_pri_keys?
    query = session.query(
        models.Trip, models.StopEvent) \
        .filter(models.Trip.route_pri_key.in_(route_id_to_route_pri_key.values()))\
        .filter(models.Trip.id == models.StopEvent.trip_pri_key) \
        .filter(models.StopEvent.future == True)\
        .all()


    db_trips = set()
    trip_id_to_db_stop_events = {}
    for (trip, stop_event) in query:
        db_trips.add(trip)
        if trip.trip_id not in trip_id_to_db_stop_events:
            trip_id_to_db_stop_events[trip.trip_id] = set()
        trip_id_to_db_stop_events[trip.trip_id].add(stop_event)



    trip_id_to_feed_stop_events = {trip['trip_id']: trip['stop_events'] for trip in data['trips']}
    for trip in data['trips']:
        trip['route_pri_key'] = route_id_to_route_pri_key[trip['route_id']]
        del trip['route_id']
        del trip['stop_events']
        #print(jsonutil.convert_for_http(trip))

    persisted_trips = syncutil.sync(models.Trip, db_trips, data['trips'], ['trip_id'])

    stop_ids = set()
    for trip in persisted_trips:
        stop_ids.update([stop_event['stop_id']
                         for stop_event
                         in trip_id_to_feed_stop_events[trip.trip_id]])

    query = session.query(models.Stop.stop_id, models.Stop.id) \
        .filter(models.Stop.stop_id.in_(stop_ids)) \
        .all()
    stop_id_to_stop_pri_key = {stop_id: stop_pri_key for (stop_id, stop_pri_key) in query}

    for trip in persisted_trips:
        stop_events = trip_id_to_feed_stop_events[trip.trip_id]
        db_stop_events = trip_id_to_db_stop_events.get(trip.trip_id, [])
        for stop_event in stop_events:
            stop_event['stop_pri_key'] = stop_id_to_stop_pri_key[stop_event['stop_id']]
            stop_event['trip_pri_key'] = trip.id
            del stop_event['stop_id']

        archive_function = archive_function_factory(trip.current_stop_sequence)

        syncutil.sync(models.StopEvent, db_stop_events, stop_events,
                      ['stop_pri_key'],
                      delete_function=archive_function)


        #print('Updated trip {}'.format(trip.trip_id))
        #print(trip.trip_id)
        #print(db_stop_events)
        #print(jsonify(trip_id_to_stop_events[trip.trip_id]))

        #break;
    #print([t1, t2, t3])
    #print('4.5 {}'.format(time.time()))
