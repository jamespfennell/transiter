import importlib
#from .protobuf import gtfs_realtime_pb2
#from .protobuf import nyc_subway_pb2
from google.transit import gtfs_realtime_pb2
import json
import datetime
from ..data import dbschema
from ..data import dbsync
from ..data import dbconnection

def jsonify(data):
    return json.dumps(data, indent=2, separators=(',', ': '), default=json_serial)
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, dbschema.Base):
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
            print('Could not generate trip_uid; skipping.')
            print(e)
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
                    'current_stop_sequence': None,
                    'last_update_time': None
                    }

            trips[trip_uid] = trip_data

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
        if trip_data['current_stop_sequence'] is not None and 'stop_events' in trip_data:
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
    print('Parsing complete.')
    return response



# Rename pb2_to_json
def gtfs_to_json(content, extension=None):
    if extension is not None:
        extension.activate()
    gtfs_feed = gtfs_realtime_pb2.FeedMessage()
    gtfs_feed.ParseFromString(content)
    return(_parse_protobuf_message(gtfs_feed))

def _identity(value):
    return value

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
def sync_to_db(data):

    # get all the routes first

    session = dbconnection.get_session()
    route_id_to_route = {route.route_id: route for route in
                         session.query(dbschema.Route).filter(dbschema.Route.route_id.in_(data['route_ids']))}
    route_pri_keys = [route.id for route in route_id_to_route.values()]
    print(jsonify(route_id_to_route))

    stop_ids = set()
    trip_id_to_stop_events = {}
    for trip in data['trips']:
        for stop_event in trip['stop_events']:
            stop_ids.add(stop_event['stop_id'])
        trip_id_to_stop_events[trip['trip_id']] = trip['stop_events']
        del trip['stop_events']

        trip['route'] = route_id_to_route[trip['route_id']]
        del trip['route_id']

        #trip['start_time'] = timestamp_to_datetime(trip['start_time'])
        #trip['last_update_time'] = timestamp_to_datetime(trip['last_update_time'])


    stop_id_to_stop = {
        stop.stop_id: stop for
        stop in session.query(dbschema.Stop).filter(dbschema.Stop.stop_id.in_(stop_ids))
    }

    db_trips = session.query(dbschema.Trip).filter(dbschema.Trip.route_pri_key.in_(route_pri_keys)).all()
    trips = dbsync.sync(dbschema.Trip, db_trips, data['trips'], ['trip_id'])

    for trip in trips:
        db_stop_events = session.query(dbschema.StopEvent).filter(dbschema.StopEvent.trip_pri_key == trip.id).filter(dbschema.StopEvent.future == True).all()

        archive_function = archive_function_factory(trip.current_stop_sequence)

        # Get rid of this -> should be in the restructure function
        for stop_event in trip_id_to_stop_events[trip.trip_id]:

            stop_event['trip'] = trip
            stop_event['stop_pri_key'] = stop_id_to_stop[stop_event['stop_id']].id

            del stop_event['stop_id']


        dbsync.sync(dbschema.StopEvent, db_stop_events,
                    trip_id_to_stop_events[trip.trip_id],
                    ['stop_pri_key'],
                    delete_function=archive_function)

        print('Updated trip {}'.format(trip.trip_id))
        #print(trip.trip_id)
        #print(db_stop_events)
        #print(jsonify(trip_id_to_stop_events[trip.trip_id]))

        #break;
