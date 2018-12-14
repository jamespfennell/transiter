from transiter.data import database
from transiter.data.dams import genericqueries
from transiter import models
from sqlalchemy import func


def create(entity=None):
    return genericqueries.create(models.System, entity)


def delete_by_id(id_):
    """
    Delete an entity from the DB whose ID is given
    :param id_:
    :return: True if an entity was found and deleted, false if no such
     entity exists
    """
    entity = get_by_id(id_)
    if entity is None:
        return False
    session = database.get_session()
    session.delete(entity)
    return True


def list_all():
    yield from genericqueries.list_all(models.System, models.System.id)


def get_by_id(id_):
    return genericqueries.get_by_id(models.System, id_)


def _count_child_entity_in_system(system_id, Model):
    session = database.get_session()
    query = session.query(func.count(Model.pk)) \
        .filter(Model.system_id == system_id)
    return query.one()[0]


def count_stops_in_system(system_id):
    return _count_child_entity_in_system(system_id, models.Stop)


def count_routes_in_system(system_id):
    return _count_child_entity_in_system(system_id, models.Route)


def count_feeds_in_system(system_id):
    return _count_child_entity_in_system(system_id, models.Feed)
