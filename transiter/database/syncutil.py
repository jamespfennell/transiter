from transiter.database import connection
from transiter.database import models


def delete_from_db(session, entity):
    session.delete(entity)


def sync(DbObject, db_entities, new_entities, keys, delete_function=delete_from_db):
    """
    This sync function only goes to one level

    DbObject: the SqlAlchemy database object
    db_entities: list of classes of type DbObject
    new_entries: list of dictionaries mapping keys to values
    keys: list of keys
    """

    id_to_db_entity = {}
    for db_entity in db_entities:
        id = tuple(getattr(db_entity, key) for key in keys)
        id_to_db_entity[id] = db_entity

    id_to_new_entity = {}
    for new_entity in new_entities:
        if new_entity is None:
            continue
        id = tuple(new_entity[key] for key in keys)
        id_to_new_entity[id] = new_entity

    db_ids = set(id_to_db_entity.keys())
    new_ids = set(id_to_new_entity.keys())
    ids_to_delete = db_ids - new_ids
    ids_to_create = new_ids - db_ids

    session = connection.get_session()

    for id in ids_to_delete:
        delete_function(session, id_to_db_entity[id])
        del id_to_db_entity[id]

    for id in ids_to_create:
        new_entity = DbObject()
        session.add(new_entity)
        id_to_db_entity[id] = new_entity

    for id, db_entity in id_to_db_entity.items():
        new_entity = id_to_new_entity[id]
        for key, new_value in new_entity.items():
            setattr(db_entity, key, new_value)

    return list(id_to_db_entity.values())



def sync_trips(data):


    #print('Beginning the mega query')



    session = connection.get_session()

    # TODO: why do I have all() here?
    # TODO: filter on transit system
    query = session.query(models.Route.route_id, models.Route.id) \
        .filter(models.Route.route_id.in_(data['route_ids'])) \
        .all()
    route_id_to_route_pri_key = {route_id: route_pri_key for (route_id, route_pri_key) in query}

    # TODO Investigate breaking this up into two queries
    # Should be easy as can find the stop events using the trip_pri_keys?
    query = session.query(
        models.Trip, models.StopEvent) \
        .filter(models.Trip.route_pri_key.in_(route_id_to_route_pri_key.values())) \
        .filter(models.Trip.id == models.StopEvent.trip_pri_key) \
        .filter(models.StopEvent.future == True) \
        .all()


    db_trips = set()
    trip_id_to_db_stop_events = {}
    for (trip, stop_event) in query:
        db_trips.add(trip)
        if trip.trip_id not in trip_id_to_db_stop_events:
            trip_id_to_db_stop_events[trip.trip_id] = set()
        trip_id_to_db_stop_events[trip.trip_id].add(stop_event)



    trip_id_to_feed_stop_events = {trip['trip_id']: trip['stop_events'] for trip in data['trips']}
    trips_to_persist = []
    for trip in data['trips']:
        if trip['route_id'] not in route_id_to_route_pri_key:
            print('Unknown route {}; known ids: {}'.format(trip['route_id'],
                                                           ', '.join(route_id_to_route_pri_key.keys())))
            continue
        trip['route_pri_key'] = route_id_to_route_pri_key[trip['route_id']]
        del trip['route_id']
        del trip['stop_events']
        trips_to_persist.append(trip)
        #print(jsonutil.convert_for_http(trip))

    persisted_trips = sync(models.Trip, db_trips, trips_to_persist, ['trip_id'])

    stop_ids = set()
    for trip in persisted_trips:
        stop_ids.update([stop_event['stop_id']
                         for stop_event
                         in trip_id_to_feed_stop_events[trip.trip_id]])

    query = session.query(models.Stop.stop_id, models.Stop.id) \
        .filter(models.Stop.stop_id.in_(stop_ids)) \
        .all()
    stop_id_to_stop_pri_key = {stop_id: stop_pri_key for (stop_id, stop_pri_key) in query}

    unknown_stop_ids = set()
    for trip in persisted_trips:
        stop_events = trip_id_to_feed_stop_events[trip.trip_id]
        db_stop_events = trip_id_to_db_stop_events.get(trip.trip_id, [])

        buggy_indices = set()
        for index, stop_event in enumerate(stop_events):
            stop_id = stop_event['stop_id']
            if stop_id not in stop_id_to_stop_pri_key:
                buggy_indices.add(index)
                unknown_stop_ids.add(stop_id)
                continue
            stop_event['stop_pri_key'] = stop_id_to_stop_pri_key[stop_event['stop_id']]
            stop_event['trip_pri_key'] = trip.id
            del stop_event['stop_id']

        for index in buggy_indices:
            stop_events[index] = None

        archive_function = archive_function_factory(trip.current_stop_sequence)

        sync(models.StopEvent, db_stop_events, stop_events,
                      ['stop_pri_key'],
                      delete_function=archive_function)


        #print('Updated trip {}'.format(trip.trip_id))
        #print(trip.trip_id)
        #print(db_stop_events)
        #print(jsonify(trip_id_to_stop_events[trip.trip_id]))

        #break;
    #print([t1, t2, t3])
    #print('4.5 {}'.format(time.time()))
    if len(unknown_stop_ids) > 0:
        print('During parsing found {} unknown stop_ids: {}'.format(len(unknown_stop_ids), ', '.join(unknown_stop_ids)))


def archive_function_factory(cutoff):
    def archive_function(session, stop_event):
        #print(stop_event)
        if cutoff is not None and stop_event.sequence_index < cutoff:
            stop_event.future = False
        else:
            session.delete(stop_event)
    return archive_function