from typing import Optional

from sqlalchemy import func, sql

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries


def create(entity=None):
    """
    Create a new System.

    :param entity: An optional System to persist
    :return: the persisted System
    """
    return genericqueries.create(models.System, entity)


def delete_by_id(id_):
    """
    Delete a System from the DB whose ID is given.

    :return: True if an entity was found and deleted, false if no such
     entity exists
    """
    session = dbconnection.get_session()
    entity = get_by_id(id_)
    if entity is None:
        return False
    session.delete(entity)
    return True


def list_all():
    """
    List all Systems in the database.
    """
    return genericqueries.list_all(models.System, models.System.id)


def get_by_id(id_, only_return_active=False) -> Optional[models.System]:
    """
    Get a system by its ID.
    """
    system = genericqueries.get_by_id(models.System, id_)
    if system is None:
        return None
    if only_return_active and system.status != system.SystemStatus.ACTIVE:
        return None
    return system


def set_auto_update_enabled(system_id, auto_update_enabled) -> bool:
    """
    Set the auto update enabled flag for a system.

    Returns a boolean denoting whether the system exists.
    """
    session = dbconnection.get_session()
    system_exists = session.query(
        sql.exists().where(models.System.id == system_id)
    ).scalar()
    if not system_exists:
        return False
    (
        session.query(models.System)
        .filter(models.System.id == system_id)
        .update({"auto_update_enabled": auto_update_enabled})
    )
    return True


def _count_child_entity_in_system(system_id, Model):
    """
    Return the number of entities of a certain type that are children of a System.

    :param system_id: the system's ID
    :param Model: the model type: Trip, Route or Stop
    :return: the integer count
    """
    session = dbconnection.get_session()
    query = (
        session.query(func.count(Model.pk))
        .filter(Model.system_pk == models.System.pk)
        .filter(models.System.id == system_id)
    )
    return query.one()[0]


def count_stops_in_system(system_id):
    """
    Return the number of Stops in a system.

    :param system_id: the system's ID
    :return: the integer count
    """
    return _count_child_entity_in_system(system_id, models.Stop)


def count_routes_in_system(system_id):
    """
    Return the number of Routes in a system.

    :param system_id: the system's ID
    :return: the integer count
    """
    return _count_child_entity_in_system(system_id, models.Route)


def count_feeds_in_system(system_id):
    """
    Return the number of Feeds in a system.

    :param system_id: the system's ID
    :return: the integer count
    """
    return _count_child_entity_in_system(system_id, models.Feed)


def list_all_alerts_associated_to_system(system_pk):
    """
    List all of the alerts associated directly to a system.

    This does *not* return alerts that are associated other entities in the system

    :param system_id: the system's ID
    :return: list of Alerts
    """
    session = dbconnection.get_session()
    query = session.query(models.Alert).filter(models.Alert.system_pk == system_pk)
    return query.all()
