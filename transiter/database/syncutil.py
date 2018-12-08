from transiter.database import connection
from transiter import models
from transiter.database.daos import route_dao, trip_dao, stop_dao


def copy_pks(source_models, target_models, id_keys, pk_key='pk'):
    # In this function we use dictionaries to gain the efficiency of sets
    # but without relying on a hash function being defined for the models
    new_models = {}
    updated_models = {}

    def model_id(model):
        return tuple(getattr(model, id_key) for id_key in id_keys)

    id_to_source_model = {model_id(model): model for model in source_models}

    for target_model in target_models:
        id_ = tuple(getattr(target_model, id_key) for id_key in id_keys)
        source_model = id_to_source_model.get(id_, None)
        if source_model is None:
            new_models[id_] = target_model
        else:
            target_model.__setattr__(pk_key, getattr(source_model, pk_key))
            updated_models[id_] = (target_model, source_model)
            del id_to_source_model[id_]

    return (
        id_to_source_model.values(),
        updated_models.values(),
        new_models.values(),
    )


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
        print('here')
        print(db_entity)

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


def _transform_trips(system_id, route_ids, new_trips):

    route_id_to_route_pk = route_dao.get_id_to_pk_map(system_id, route_ids)
    route_ids = route_id_to_route_pk.keys()

    new_trips_to_persist = []
    trip_key_to_stop_events = {}
    for new_trip in new_trips:
        if new_trip['route_id'] not in route_ids:
            # TODO: log this
            continue
        route_pk = route_id_to_route_pk[new_trip['route_id']]
        new_trip['route_pk'] = route_pk
        trip_key_to_stop_events[(route_pk, new_trip['id'])] = new_trip['stop_events']
        del new_trip['route_id']
        del new_trip['stop_events']
        new_trips_to_persist.append(new_trip)

    return new_trips_to_persist, trip_key_to_stop_events


def _persist_trips(system_id, route_ids, new_trips):
    old_trips = trip_dao.list_all_in_routes(system_id, route_ids)
    return sync(
        models.Trip,
        old_trips,
        new_trips,
        ['route_pk', 'id']
    )


def _transform_stop_events(trip_pk, feed_stop_events,
                           stop_id_alias_to_stop_id, stop_id_to_stop_pk):
    stop_events_to_persist = []
    unknown_stop_ids = set()
    for feed_stop_event in feed_stop_events:
        stop_event = {key: value for (key, value) in feed_stop_event.items()}
        stop_id = stop_event['stop_id']
        if stop_id_to_stop_pk.get(stop_id, None) is None:
            if stop_id_alias_to_stop_id.get(stop_id, None) is None:
                unknown_stop_ids.add(stop_id)
                continue
            stop_event['stop_id_alias'] = stop_id
            stop_id = stop_id_alias_to_stop_id[stop_id]

        stop_event['future'] = True
        stop_event['stop_pk'] = stop_id_to_stop_pk[stop_id]
        stop_event['trip_pk'] = trip_pk
        del stop_event['stop_id']

        stop_events_to_persist.append(stop_event)

    return stop_events_to_persist, unknown_stop_ids


def _persist_stop_events(old_stop_events, new_stop_events):

    min_stop_sequence = None
    if len(new_stop_events) > 0:
        min_stop_sequence = new_stop_events[0]['stop_sequence']
    archive_function = archive_function_factory(min_stop_sequence)

    return sync(
        models.StopTimeUpdate,
        old_stop_events,
        new_stop_events,
        ['stop_pk'],
        delete_function=archive_function
    )


#def sync_trips(system_id, route_ids, feed_trips)
def sync_trips(data, system_id='nycsubway'):

    (new_trips, trip_key_to_feed_stop_events) = _transform_trips(
        system_id, data['route_ids'], data['trips'])
    persisted_trips = _persist_trips(
        system_id, data['route_ids'], new_trips)

    trip_pk_to_db_stop_events = trip_dao.get_trip_pk_to_future_stop_events_map(
        [trip.pk for trip in persisted_trips])

    stop_ids = set()
    for feed_stop_events in trip_key_to_feed_stop_events.values():
        for feed_stop_event in feed_stop_events:
            stop_ids.add(feed_stop_event['stop_id'])
    # TODO remove alias
    stop_id_alias_to_stop_id = {}
    stop_ids.update(stop_id_alias_to_stop_id.values())
    stop_id_to_stop_pri_key = stop_dao.get_id_to_pk_map(system_id, stop_ids)

    all_unknown_stop_ids = set()
    for trip in persisted_trips:
        (stop_events_to_persist, unknown_stop_ids) = _transform_stop_events(
            trip.pk,
            trip_key_to_feed_stop_events[(trip.route_pk, trip.id)],
            stop_id_alias_to_stop_id,
            stop_id_to_stop_pri_key
        )
        _persist_stop_events(
            trip_pk_to_db_stop_events.get(trip.pk, []),
            stop_events_to_persist
        )
        all_unknown_stop_ids.update(unknown_stop_ids)

    """
    TODO: log this
    if len(unknown_stop_ids) > 0:
        print('During parsing found {} unknown stop_ids: {}'.format(len(unknown_stop_ids), ', '.join(unknown_stop_ids)))
    """


def archive_function_factory(cutoff):
    def archive_function(session, stop_event):
        if cutoff is not None and stop_event.stop_sequence < cutoff:
            stop_event.future = False
        else:
            session.delete(stop_event)
    return archive_function
