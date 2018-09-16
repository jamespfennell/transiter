import importlib
#from .protobuf import gtfs_realtime_pb2
#from .protobuf import nyc_subway_pb2
from google.transit import gtfs_realtime_pb2
import json
import datetime
from ..data import schema
from ..data import dbsync
from ..data import dbconnection

def jsonify(data):
    return json.dumps(data, indent=2, separators=(',', ': '), default=json_serial)
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, schema.Base):
        return str(obj)
    raise TypeError ("Type %s not serializable" % type(obj))




class GtfsExtension():

    def __init__(self, pb_module, base_module):
        self._pb_module = pb_module
        self._base_module = base_module

    def activate(self):
        importlib.import_module(self._pb_module, self._base_module)



def restructure(content):
    return content


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
        else:
            parsing_function = _identity

        # If this is a repeated field
        if descriptor.label == descriptor.LABEL_REPEATED:
            parsed_value = [parsing_function(v) for v in value]
        else:
            parsed_value = parsing_function(value)

        d[descriptor.name] = parsed_value

    return d


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
def sync_to_db(data):

    # get all the routes first

    session = dbconnection.get_session()
    route_id_to_route = {route.route_id: route for route in
        session.query(schema.Route).filter(schema.Route.route_id.in_(data['route_ids']))}
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

        trip['start_time'] = timestamp_to_datetime(trip['start_time'])
        trip['last_update_time'] = timestamp_to_datetime(trip['last_update_time'])


    stop_id_to_stop = {
        stop.stop_id: stop for
        stop in session.query(schema.Stop).filter(schema.Stop.stop_id.in_(stop_ids))
    }

    db_trips = session.query(schema.Trip).filter(schema.Trip.route_pri_key.in_(route_pri_keys)).all()
    trips = dbsync.sync(schema.Trip, db_trips, data['trips'], ['trip_id'])

    for trip in trips:
        db_stop_events = session.query(schema.StopEvent).filter(schema.StopEvent.trip_pri_key==trip.id).filter(schema.StopEvent.future == True).all()

        archive_function = archive_function_factory(trip.current_stop_sequence)

        # Get rid of this -> should be in the restructure function
        for stop_event in trip_id_to_stop_events[trip.trip_id]:
            for key in ['arrival_time', 'departure_time', 'last_update_time']:
                if key in stop_event and stop_event[key] is not None:
                    stop_event[key] = timestamp_to_datetime(stop_event[key])

            stop_event['trip'] = trip
            stop_event['stop_pri_key'] = stop_id_to_stop[stop_event['stop_id']].id

            del stop_event['stop_id']


        dbsync.sync(schema.StopEvent, db_stop_events,
            trip_id_to_stop_events[trip.trip_id],
            ['stop_pri_key'],
            delete_function=archive_function)

        print('Updated trip {}'.format(trip.trip_id))
        #print(trip.trip_id)
        #print(db_stop_events)
        #print(jsonify(trip_id_to_stop_events[trip.trip_id]))

        #break;
