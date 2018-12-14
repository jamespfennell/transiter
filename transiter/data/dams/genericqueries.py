from transiter.data import database
from transiter import models


def list_all(DbObject: models.Base, order_by_field=None):
    session = database.get_session()
    query = session.query(DbObject)
    if order_by_field is not None:
        query = query.order_by(order_by_field)
    for row in query:
        yield row


def get_by_id(DbObject: models.Base, id_):
    session = database.get_session()
    return (
        session.query(DbObject)
            .filter(DbObject.id == id_)
            .one_or_none()
    )


def list_all_in_system(DbObject: models.Base, system_id, order_by_field=None):
    session = database.get_session()
    query = session.query(DbObject).filter(DbObject.system_id == system_id)
    if order_by_field is not None:
        query = query.order_by(order_by_field)
    for row in query:
        yield row


def get_in_system_by_id(DbObject: models.Base, system_id, id_):
    session = database.get_session()
    return (
        session.query(DbObject)
        .filter(DbObject.system_id == system_id)
        .filter(DbObject.id == id_)
        .one_or_none()
    )


def get_id_to_pk_map(DbObject: models.Base, system_id, ids):
    id_to_pk = {id_: None for id_ in ids}
    session = database.get_session()
    query = (
        session.query(DbObject.id, DbObject.pk)
        .filter(DbObject.id.in_(ids))
        .filter(DbObject.system_id == system_id)
        .all()
    )
    for (id_, pk) in query:
        id_to_pk[id_] = pk
    return id_to_pk


