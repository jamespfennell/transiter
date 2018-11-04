from transiter.database import connection
from transiter.database import models
from transiter.database.daos import route_dao, trip_dao, stop_dao


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


def _persist_trips(system_id, route_ids, new_trips):

    route_id_to_route_pk = route_dao.get_id_to_pk_map(system_id, route_ids)
    route_ids = route_id_to_route_pk.keys()

    old_trips = trip_dao.list_all_in_routes_by_pk(
        list(route_id_to_route_pk.values()))

    new_trips_to_persist = []
    for new_trip in new_trips:
        if new_trip['route_id'] not in route_ids:
            # TODO: log this
            # print('Unknown route {}; known ids: {}'.format(
            #    trip['route_id'], ', '.join(route_ids)))
            continue
        new_trip['route_pri_key'] = route_id_to_route_pk[new_trip['route_id']]
        del new_trip['route_id']
        del new_trip['stop_events']
        new_trips_to_persist.append(new_trip)

    persisted_trips = sync(
        models.Trip,
        old_trips,
        new_trips_to_persist,
        ['route_pri_key', 'trip_id'])
    return persisted_trips


def _persist_stop_events(trip_pk, old_stop_events, new_stop_events,
                         stop_id_alias_to_stop_id, stop_id_to_stop_pk):
    unknown_stop_ids = set()
    buggy_indices = set()
    min_stop_sequence = None
    for index, stop_event in enumerate(new_stop_events):

        stop_id = stop_event['stop_id']
        if stop_id not in stop_id_to_stop_pk:
            if stop_id not in stop_id_alias_to_stop_id:
                buggy_indices.add(index)
                unknown_stop_ids.add(stop_id)
                continue
            stop_event['stop_id_alias'] = stop_id
            stop_id = stop_id_alias_to_stop_id[stop_id]

        stop_event['future'] = True
        stop_event['stop_pri_key'] = stop_id_to_stop_pk[stop_id]
        stop_event['trip_pri_key'] = trip_pk
        del stop_event['stop_id']

        this_stop_sequence = stop_event.get('stop_sequence')
        if min_stop_sequence is None or min_stop_sequence > this_stop_sequence:
            min_stop_sequence = this_stop_sequence

    for index in buggy_indices:
        new_stop_events[index] = None

    archive_function = archive_function_factory(min_stop_sequence)

    sync(
        models.StopEvent,
        old_stop_events,
        new_stop_events,
        ['stop_pri_key'],
        delete_function=archive_function
    )

    return unknown_stop_ids


#def sync_trips(system_id, route_ids, feed_trips)
def sync_trips(data, system_id='nycsubway'):

    # NOTE: the _persist_trips method detaches the stop_events from the feed
    # trips so it is necessary to save the stop_events before invoking it.
    trip_key_to_feed_stop_events = {
        (trip['route_id'], trip['trip_id']): trip['stop_events']
        for trip in data['trips']
    }
    persisted_trips = _persist_trips(system_id, data['route_ids'], data['trips'])

    trip_pk_to_feed_stop_events = {}
    for trip in persisted_trips:
        key = (trip.route_id, trip.trip_id)
        assert key in trip_key_to_feed_stop_events
        trip_pk_to_feed_stop_events[trip.id] = trip_key_to_feed_stop_events[key]

    trip_pk_to_db_stop_events = trip_dao.get_trip_pk_to_future_stop_events_map(
        [trip.id for trip in persisted_trips])

    stop_ids = set()
    for trip in persisted_trips:
        stop_ids.update(
            [stop_event['stop_id'] for stop_event
                in trip_pk_to_feed_stop_events[trip.id]])
    stop_id_alias_to_stop_id = stop_dao.get_stop_id_alias_to_stop_id_map(
        system_id, stop_ids)
    stop_ids.update(stop_id_alias_to_stop_id.values())
    stop_id_to_stop_pri_key = stop_dao.get_id_to_pk_map(system_id, stop_ids)

    all_unknown_stop_ids = set()
    for trip in persisted_trips:
        unknown_stop_ids = _persist_stop_events(
            trip.id,
            trip_pk_to_feed_stop_events[trip.id],
            trip_pk_to_db_stop_events.get(trip.id, []),
            stop_id_alias_to_stop_id,
            stop_id_to_stop_pri_key
        )
        all_unknown_stop_ids.update(unknown_stop_ids)

    """
    TODO: log this
    if len(unknown_stop_ids) > 0:
        print('During parsing found {} unknown stop_ids: {}'.format(len(unknown_stop_ids), ', '.join(unknown_stop_ids)))
    """


def archive_function_factory(cutoff):
    def archive_function(session, stop_event):
        if cutoff is not None and stop_event.sequence_index < cutoff:
            stop_event.future = False
        else:
            session.delete(stop_event)
    return archive_function
