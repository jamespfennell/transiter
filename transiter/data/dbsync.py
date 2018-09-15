from . import dbconnection


def sync(DbObject, db_entities, new_entities, keys):
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
        id = tuple(new_entity[key] for key in keys)
        id_to_new_entity[id] = new_entity

    db_ids = set(id_to_db_entity.keys())
    new_ids = set(id_to_new_entity.keys())
    ids_to_delete = db_ids - new_ids
    ids_to_create = new_ids - db_ids

    session = dbconnection.get_session()

    for id in ids_to_delete:
        session.delete(id_to_db_entities[id])
        del id_to_db_entities[id]

    for id in ids_to_create:
        new_entity = DbObject()
        session.add(new_entity)
        id_to_db_entity[id] = new_entity

    for id, db_entity in id_to_db_entity.items():
        new_entity = id_to_new_entity[id]
        for key, new_value in new_entity.items():
            setattr(db_entity, key, new_value)

    return id_to_db_entity.values()
