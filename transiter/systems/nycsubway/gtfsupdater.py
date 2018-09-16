"""
Need to write
 - a general GTFS -> JSON converter.
    - the converter needs to handle extensions

Then write
 - Code to transform the MTA data into something like the DB entities

Then pass this JSON to dbsync .... maybe twice, once for trips, once
    for stop events

Need to activate the DB entities

"""


import pytz
#import os
import datetime
#import time
#import hashlib
import json

def jsonify(data):
    return json.dumps(data, indent=2, separators=(',', ': '), default=json_serial)
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


from ...utils import gtfsutil


def update(feed, system, content):

    nyc_subway_gtfs_extension = gtfsutil.GtfsExtension(
        '..nyc_subway_pb2',
        __name__
        )
    feed_json = gtfsutil.gtfs_to_json(content, nyc_subway_gtfs_extension)
    feed_json = gtfsutil.restructure(feed_json)



    # transformed_json = gtfsutil.transform(feed_json,
    #    trip_extenion='a', stop_event_extension='b')
    # fix_nyc_subway_data(transformed_json)
    # ....swap out DB bobjects
    # ....and then sync

    db_json = interpret_nyc_subway_gtfs_feed(feed_json)

    gtfsutil.sync_to_db(db_json)
    # For the sync step, compare with all route ids in db_json['route_ids']


    #    print(jsonify(db_json))



def interpret_nyc_subway_gtfs_feed(data):
    """
    Input: gtfs feed in json format
    Output: json containing data represented in the same way as the Transiter DB
    This is where NYC Subway specific logic/intepretation/cleanin goes
    """

    header = data['header']
    # Read header information from the feed: the time it was created, and the routes contained within.
    feed_timestamp = header['timestamp']
    if feed_timestamp == 0:
        print('Invalid feed, raw feed text:')
        print(gtfs_feed)
        raise InvalidGTFSFile('Invalid GTFS file.')
    feed_time = timestamp_to_datetime(feed_timestamp)
    feed_route_ids = set()
    actual_feed_route_ids = set()
    nyct_feed_header = header['nyct_feed_header']
    for route_info in nyct_feed_header['trip_replacement_period']:
        route_id = route_info['route_id']
        # The routes declared in the feeds are buggy
        # and don't correspond exactly to what's in the feed.
        if route_id == "S":
            feed_route_ids.add("GS")
        elif route_id == "5":
            feed_route_ids.add("5")
        elif route_id == "6":
            feed_route_ids.add("6")
            feed_route_ids.add("6X")
        elif route_id == "SI":
            feed_route_ids.add("SS")
            feed_route_ids.add("SI")
        else:
            feed_route_ids.add(route_id)

    if ("6" in feed_route_ids) and ("7" in feed_route_ids):
        feed_route_ids.discard("7")

    # Now iterate over trips in the feed, placing the trip data in memory
    # Each trip corresponds to two different entities in the feed file: a trip_update entity and a vehicle entity
    # (the latter provided only if the trip has been assigned). Both entities contain basic trip information in a
    # trip field.
    trips = {}
    trips_with_fake_first_stop = set()
    for entity in data['entity']:
        # Based on which type of entity, the location of the trip data is different.
        if 'trip_update' in entity:
            trip = entity['trip_update']['trip']
        if 'vehicle' in entity:
            trip = entity['vehicle']['trip']

        # Generate the trip_uid. First determine the direction
        if trip['nyct_trip_descriptor']['direction'] == 1:
            direction = 'N'
        else:
            direction = 'S'
        # There is a bug (as of Jan 31 2018) that southbound E trains are marked as northbound and vice-versa.
        # So for E trains, the direction needs to be inverted
        # Also for 5 trains, the id 5X is not meaningful so it's just mapped to 5
        if trip['route_id'] == 'E':
            direction = invert_direction(direction)
        if trip['route_id'] == '5X':
            trip['route_id'] = '5'
        if trip['route_id'] not in feed_route_ids:
            # Actually in the logs I'm seeing a lot of route_id = ''
            print('Found trip in feed with route "{}" not present in routes declared in header.'.format(trip.route_id))
            #with open('tmp/problems-bad-routes.txt','a') as f:
            #    f.write('{} - {}\n'.format(trip.route_id, list(feed_route_ids)))
            continue
        actual_feed_route_ids.add(trip['route_id'])

        # Now generate the trip_uid and the start time
        try:
            trip_uid = generate_trip_uid(
                trip['trip_id'],
                trip['start_date'],
                trip['route_id'],
                direction
                )
        except Exception as e:
            print('Could not generate trip_uid; skipping.')
            print(e)
            continue

        # Checking for buggy trains: trains whose start time is in the past but have not been assigned
        start_time = int(generate_trip_start_time(trip['trip_id'], trip['start_date']).timestamp())
        if trip['nyct_trip_descriptor']['is_assigned'] is False and (start_time - feed_timestamp <-300):
            print('Buggy train {}; skipping.'.format(trip_uid))
            continue

        # If the basic trip_uid settings have already been imported, do nothing; otherwise, import then.
        if trip_uid in trips:
            trip_data = trips[trip_uid]
        else:
            trip_data = {
                    'trip_id' : trip_uid,
                    'route_id' : trip['route_id'],
                    'direction' : direction,
                    'start_time' : start_time,
                    'train_id' : trip['nyct_trip_descriptor']['train_id'],
                    'is_assigned' : trip['nyct_trip_descriptor']['is_assigned'],
                    'last_update_time' : feed_time,
                    'current_status' : None,
                    'current_stop_sequence' : None
                    }
            if trip['route_id'] == "":
                # Probaby this was already caught above already
                print('Buggy train {} (no route id); skipping.'.format(trip_uid))
                continue
            trips[trip_uid] = trip_data

        if 'vehicle' in entity:
            current_stop_sequence = entity['vehicle']['current_stop_sequence']
            update_time = timestamp_to_datetime(entity['vehicle']['timestamp'])
            trip_data.update({
                'last_update_time' : update_time,
                'current_status' : entity['vehicle']['current_status'],
                'current_stop_sequence' : entity['vehicle']['current_stop_sequence']
            })



        if 'trip_update' in entity:
            trip_data['stop_events'] = []
            current_stop_sequence = 0
            for stop_time_update in entity['trip_update']['stop_time_update']:
                # There is a bug (as of Jan 31 2018) that southbound E trains are marked as northbound and vice-versa.
                # So for E trains, the direction needs to be inverted
                direction = stop_time_update['stop_id'][3:4]
                if trip['route_id'] == 'E':
                    direction = invert_direction(direction)
                # Basic information
                stop_event_data = {
                        #'trip_id' : trip_uid,
                        'stop_id' : stop_time_update['stop_id'][0:3],
                        'direction' : direction,
                        'future' : True,
                        }


                # Arrival/departure time information
                if 'arrival' in stop_time_update and +stop_time_update['arrival']['time'] != 0:
                    stop_event_data['arrival_time'] = timestamp_to_datetime(stop_time_update['arrival']['time'])
                else:
                    stop_event_data['arrival_time'] = None
                if 'departure' in stop_time_update and stop_time_update['departure']['time'] != 0:
                    stop_event_data['departure_time'] = timestamp_to_datetime(stop_time_update['departure']['time'])
                else:
                    stop_event_data['departure_time'] = None

                # Track information
                nyct_stop_time_update = stop_time_update['nyct_stop_time_update']
                stop_event_data['scheduled_track'] = nyct_stop_time_update['scheduled_track']
                if 'actual_track' in nyct_stop_time_update:
                    stop_event_data['actual_track'] = nyct_stop_time_update['actual_track']
                else:
                    stop_event_data['actual_track'] = None

                # Sequence index data (provisional if the trip has been assigned)
                current_stop_sequence += 1
                stop_event_data['sequence_index'] = current_stop_sequence

                trip_data['stop_events'].append(stop_event_data)


        # This following condition checks that both the vehicle and trip_update entities respectively have been imported.
        # If they have been, the sequence indices should be updated to factor in the number of stops already passed
        # (which is given by the current_stop_sequence field in the vehicle entity
        if trip_data['current_stop_sequence'] is not None and 'stop_events' in trip_data:
            # Update the stop sequence indices
            current_stop_sequence = trip_data['current_stop_sequence']
            for stop_event_data in trip_data['stop_events']:
                current_stop_sequence += 1
                stop_event_data['sequence_index'] = current_stop_sequence

            # There is a 'problem' with the MTA feed whereby a stop may be in the feed even if it has passed.
            # This happens when the feed data is only updated at stops.
            # So when going from A -> B, the train needs to reach B before noting that it has left A
            # The mark of this scenario is that the arrival time at A is the same as the update time
            # In this case then, we ignore the stop if the update time is more than 15 seconds ago -- time for the train to have left.
            # To avoid a bug, this ignoring only happens if there are more than 2 stops left.
            if len(trip_data['stop_events'])>1:
                first_stop_time = trip_data['stop_events'][0]['arrival_time']
                if first_stop_time is None:
                    first_stop_time = trip_data['stop_events'][0]['departure_time']
                if first_stop_time <= trip_data['last_update_time']:
                    if current_timestamp() - trip_data['last_update_time'].timestamp() > 15:
                        trips_with_fake_first_stop.add(trip_data['trip_id'])
                        del trip_data['stop_events'][0]

        # The last stop is given by residual information from the last for loop
        #trip_data['terminating_stop_uid'] = stop_event_data['stop_id']

    if len(trips_with_fake_first_stop) > 0:
        print('Some trips were deemed to have already left the first stop given:')
        print(trips_with_fake_first_stop)
    response = {
            'timestamp' : header['timestamp'],
            'actual_route_ids' : list(actual_feed_route_ids),
            'route_ids' : list(feed_route_ids),
            'trips' : list(trips.values())
            }
    print('Parsing complete.')
    return response



eastern = pytz.timezone('US/Eastern')


def timestamp_to_datetime(timestamp):
    return timestamp
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)



def generate_trip_start_time(trip_id, start_date):
    seconds_since_midnight = (int(trip_id[:trip_id.find('_')])//100)*60
    second = seconds_since_midnight % 60
    minute = (seconds_since_midnight // 60)%60
    hour = (seconds_since_midnight // 3600)
    year = int(start_date[0:4])
    month = int(start_date[4:6])
    day = int(start_date[6:8])
    return eastern.localize(datetime.datetime(year, month, day, hour, minute, second))

def generate_trip_uid(trip_id, start_date, route_id, direction):
    return route_id + direction + str(int(generate_trip_start_time(trip_id, start_date).timestamp()))

def invert_direction(direction):
    if direction == 'N':
        return 'S'
    else:
        return 'N'


def current_timestamp():
    return int(time.time())

"""
class InvalidGTFSFile(Exception):
    pass

def update_from_nyc_subway_gtfs_file(file_path):
    print('Updating from: {}'.format(file_path))
    print('Passing file to GTFS parser.')

    try:
        gtfs_data = parse_nyc_subway_gtfs_file(file_path)
    #except Exception as e:
    except KeyboardInterrupt as e:
        print('Invalid GTFS file.')
        print(e)
        return False



    db = database.DatabaseConnector()
    feed_time = timestamp_to_datetime(gtfs_data['timestamp'])

    sql_template = "UPDATE routes SET update_time=%s WHERE route_id IN ({})".format(','.join(['%s']*len(gtfs_data['route_ids'])))
    print(sql_template)
    db.cursor.execute(sql_template,[feed_time] + gtfs_data['route_ids'])

    print('Feed time: {}.'.format(feed_time.isoformat()))
    print('Updating routes: {}.'.format(', '.join(gtfs_data['route_ids'])))
    trips_reconciler = db.reconciler(
            'trips',
            ('trip_uid',),
            ('update_time', 'is_assigned'),
            {'route_id' : gtfs_data['route_ids']}
            )
    inserted_trips = set()
    deleted_unassigned_trips = set()

    for trip in gtfs_data['trips']:

        reconciler_key = {'trip_uid' : trip['trip_uid']}

        # If the trip has not been assigned and it is in the database, there is nothing to do as unassigned trips aren't updated.
        if (not trip['is_assigned']) and (reconciler_key in trips_reconciler):
            trips_reconciler.ignore(reconciler_key)
            continue

        # Next, ensure we're only updating the trip with new data
        # If this trip is not in the database, a key error will be raised when attempting to access the dynamic values
        try:
            prev_update_time = trips_reconciler.dynamic_values(reconciler_key)['update_time'].replace(tzinfo=datetime.timezone.utc)
            if prev_update_time > trip['update_time']:
                print('Error: attempting to update trip {} with old information.'.format(trip['trip_uid']))
                trips_reconciler.ignore(reconciler_key)
                continue
        except KeyError:
            pass

        # Detach the stop events from the trip JSON, and push the trip data to the database
        stop_events = trip['stop_events']
        del trip['stop_events']
        #print('Pushing {}'.format(trip['trip_uid']))
        #print(jsonify.jsonify(trip))
        database_action = trips_reconciler.push(trip) # =0 if nothing changed; =1 if new entry inserted; =2 if existing entry updated


        if database_action == 1:
            inserted_trips.add(trip['trip_uid'])

        # If nothing changed -- meaning the update time in the database is the same as the gtfs file -- nothing needs to be done
        if database_action:
            stop_events_reconciler = db.reconciler(
                    'stop_events',
                    ('stop_uid', ),
                    ('arrival_time', 'departure_time', 'scheduled_track', 'actual_track', 'sequence_index'),
                    {'trip_uid' : trip['trip_uid'], 'future' : '1' }
                    )

            for stop_event in stop_events:
                stop_events_reconciler.push(stop_event)

            # Iterate over the stop events in the database that haven't been changed.
            # These are of two kinds: stop events that passed, or stop events that were canceled.
            passed_stop_events = False
            for cancelled_stop_event in stop_events_reconciler.remaining():
                sequence_index = stop_events_reconciler.dynamic_values(cancelled_stop_event)['sequence_index']
                if sequence_index > trip['current_stop_sequence']:
                    stop_events_reconciler.delete(cancelled_stop_event)
                else:
                    passed_stop_events = True

            if passed_stop_events:
                # Mark any stops for this trip which are indexed before the current index to be set as pase.
                sql_template =
                    UPDATE stop_events
                    SET future='0'
                    WHERE sequence_index<=%s AND trip_uid=%s

                db.cursor.execute(sql_template, (trip['current_stop_sequence'], trip['trip_uid']))


    # Finally we examine those trips in the database which do not appear in the gtfs file
    for ended_trip in trips_reconciler.remaining():
        # If in the database the trip is not assigned, then we just delete it
        if not trips_reconciler.dynamic_values(ended_trip)['is_assigned']:
            db.delete_table_entry('stop_events', ended_trip)
            trips_reconciler.delete(ended_trip)
            deleted_unassigned_trips.add(ended_trip['trip_uid'])
            continue

        # Otherwise, we may want to keep it.
        # The scenario is that sometimes valid trips drop out of the gtfs feed for a brief time, and then reappear
        # We don't want to delete such trips.
        # Therefore, a trip that is missing from the gtfs file is not deleted if its last update time was within the last 2 minutes
        update_time_dt = trips_reconciler.dynamic_values(ended_trip)['update_time'].replace(tzinfo=datetime.timezone.utc)
        print('Potentially deleting assigned trip: ' + ended_trip['trip_uid'])
        print(' - Update time: {}.'.format(update_time_dt.isoformat()) )
        db.cursor.execute(
        ""
            SELECT trips.is_assigned, stop_events.arrival_time
            FROM trips
            INNER JOIN stop_events ON stop_events.stop_uid=trips.terminating_stop_uid AND stop_events.trip_uid=trips.trip_uid
            WHERE trips.trip_uid='{}'
            "".format(ended_trip['trip_uid']))
        (is_assigned, last_arrival_time) = db.cursor.fetchone()
        if last_arrival_time is not None:
            print(' - Arrival time at last stop: {}.'.format(last_arrival_time.isoformat()) )
            if (feed_time - update_time_dt < datetime.timedelta(minutes=2)):
                print(' - Not deleting')
                continue
        else:
            print(' - Buggy train.')
        print(' - Deleting')
        db.delete_table_entry('stop_events', ended_trip)
        trips_reconciler.delete(ended_trip)

    # If everything is good, update the database
    db.commit()

    print('Database changes committed.')
    print('Inserted the following new trips:')
    print(inserted_trips)
    print('Deleted the following previously unassigned trips:')
    print(deleted_unassigned_trips)







def timestamp_to_utc_str(ts, s = '%y/%m/%d %H:%M:%S'):
    dt = datetime.datetime.utcfromtimestamp(int(ts))
    #utc_dt = pytz.utc.localize(dt)
    return dt.strftime(s)








def realtime_data_in_database_hash(db):

    pre_str = []
    db.cursor.execute('SELECT * FROM trips ORDER BY trip_uid')
    for row in db.cursor:
        s_row = [str(col) for col in row]
        pre_str.append(', '.join(s_row))
    db.cursor.execute('SELECT * FROM stop_events WHERE future="1" ORDER BY trip_uid, stop_uid')
    for row in db.cursor:
        s_row = [str(col) for col in row]
        pre_str.append(', '.join(s_row))

    s = '\n'.join(pre_str)
    return hashlib.md5(s.encode()).hexdigest()






#db = database.DatabaseConnector()

update_from_ServiceStatusSubway_xml('./sample_data/ServiceStatusSubway-103.xml', db)

exit()


print(realtime_data_in_database_hash(db))

db.cursor.execute('DELETE FROM trips')
db.cursor.execute('DELETE FROM stop_events')
db.commit()


files = os.listdir('./sample_data/')
for file_name in files:
    print(file_name)


exit()

update_from_nyc_subway_gtfs_file('./sample_data/l-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/ace-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/bdfm-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/nqrw-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/jz-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/123456-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/7-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/sir-8.gtfs', db)
update_from_nyc_subway_gtfs_file('./sample_data/g-8.gtfs', db)
print(realtime_data_in_database_hash(db))
"""
