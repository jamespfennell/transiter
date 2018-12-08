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

