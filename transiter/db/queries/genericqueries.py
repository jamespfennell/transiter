"""
This module provides some abstract methods to remove code duplication in the DAMs.
"""
import typing
from typing import Dict, Iterable

from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

from transiter.db import dbconnection, models


def create(DbEntity: models.Base, entity=None):
    """
    Create a database entity.

    :param DbEntity: the entity's type
    :param entity: optionally an instance of this type that will instead be added
        to the session
    :return: the entity, which is in the session
    """
    session = dbconnection.get_session()
    if entity is None:
        entity = DbEntity()
    session.add(entity)
    return entity


def get_by_id(DbEntity: models.Base, id_):
    """
    Get an entity by its ID.

    :param DbEntity: the entity's type
    :param id_: the entity's ID
    :return: the entity, if it exists in the DB, or None otherwise
    """
    session = dbconnection.get_session()
    return session.query(DbEntity).filter(DbEntity.id == id_).one_or_none()


def list_in_system(DbEntity: models.Base, system_id, order_by_field=None, ids=None):
    """
    List all entities of a certain type that are in a given system. Note this method
    only works with entities that are direct children of the system.

    :param DbEntity: the entity's type
    :param system_id: the system's ID
    :param order_by_field: optional field to order the results by
    :param ids: ids to filter on
    :return: list of entities of type DbEntity
    """
    if ids is not None and len(ids) == 0:
        return []
    session = dbconnection.get_session()
    query = (
        session.query(DbEntity)
        .filter(DbEntity.system_pk == models.System.pk)
        .filter(models.System.id == system_id)
    )
    if ids is not None:
        query = query.filter(DbEntity.id.in_(ids))
    if order_by_field is not None:
        query = query.order_by(order_by_field)
    return query.all()


def get_in_system_by_id(DbEntity: models.Base, system_id, id_):
    """
    Get an entity of a certain type that is in a given system. Note this method
    only works with entities that are direct children of the system.

    :param DbEntity: the entity's type
    :param system_id: the system's ID
    :param id_: the entity's ID
    :return: list of entities of type DbEntity
    """
    session = dbconnection.get_session()
    return (
        session.query(DbEntity)
        .filter(DbEntity.system_pk == models.System.pk)
        .filter(models.System.id == system_id)
        .filter(DbEntity.id == id_)
        .options(joinedload(DbEntity.system))
        .one_or_none()
    )


def get_id_to_pk_map(
    DbEntity: models.Base, system_pk: int = None, ids: Iterable[str] = None
) -> Dict[str, int]:
    """
    Get an map of entity ID to entity PK for all entities of a given type in a system.
    Note this method only works with entities that are direct children of the system.
    """
    if ids is not None:
        ids = list(ids)
        id_to_pk = {id_: None for id_ in ids}
    else:
        id_to_pk = {}
    session = dbconnection.get_session()
    query = session.query(DbEntity.id, DbEntity.pk)
    if system_pk is not None:
        query = query.filter(DbEntity.system_pk == system_pk)
    if ids is not None:
        query = query.filter(DbEntity.id.in_(ids))
    for (id_, pk) in query.all():
        id_to_pk[id_] = pk
    return id_to_pk


# DbEntity is a class
# noinspection PyPep8Naming
def get_id_to_pk_map_by_feed_pk(DbEntity: typing.Type[models.Base], feed_pk):
    id_to_pk = {}
    session = dbconnection.get_session()
    query = (
        session.query(DbEntity.id, DbEntity.pk)
        .join(models.FeedUpdate, DbEntity.source_pk == models.FeedUpdate.pk)
        .filter(models.FeedUpdate.feed_pk == feed_pk)
    )
    for (id_, pk) in query.all():
        id_to_pk[id_] = pk
    return id_to_pk


# DbEntity is a class
# noinspection PyPep8Naming
def delete_stale_entities(
    DbEntity: typing.Type[models.Base], feed_update: models.FeedUpdate
):
    session = dbconnection.get_session()
    (
        session.query(DbEntity)
        .filter(DbEntity.source_pk == models.FeedUpdate.pk)
        .filter(models.FeedUpdate.feed_pk == feed_update.feed_pk)
        .filter(models.FeedUpdate.pk != feed_update.pk)
    ).delete(synchronize_session=False)


# DbEntity is a class
# noinspection PyPep8Naming
def list_stale_entities(
    DbEntity: typing.Type[models.Base], feed_update: models.FeedUpdate
):
    session = dbconnection.get_session()
    query = (
        session.query(DbEntity)
        .join(models.FeedUpdate, DbEntity.source_pk == models.FeedUpdate.pk)
        .filter(models.FeedUpdate.feed_pk == feed_update.feed_pk)
        .filter(models.FeedUpdate.pk != feed_update.pk)
    )
    return query.all()


def count_number_of_related_entities(relationship, instance) -> int:
    """
    Count the number of entities related to an instance along a specified relationship.
    """
    base_type = relationship.class_
    related_type = relationship.mapper.class_
    session = dbconnection.get_session()
    query = (
        session.query(func.count(1))
        .select_from(base_type)
        .join(related_type, relationship)
        .filter(getattr(base_type, "pk") == instance.pk)
    )
    return query.one()[0]
