from . import connection
from . import models

from sqlalchemy.orm.exc import NoResultFound


class _Query:

    def __init__(self, dao):
        self._dao = dao
        session = self._dao.get_session()
        self._query = session.query(self._dao._DbObj)

    def add_order_condition(self):
        if self._dao._order_field is not None:
            self._query = self._query.order_by(self._dao._order_field)

    def add_id_condition(self, entity_id):
        self._query = self._query.filter(self._dao._id_field == entity_id)

    def add_system_condition(self, system_id):
        self._query = self._query.filter(self._dao._DbObj.system_id==system_id)

    def one(self):
        try:
            return self._query.one()
        except NoResultFound:
            return None

    def __iter__(self):
        for entity in self._query:
            yield entity


class _BaseEntityDao:

    def __init__(self):
        self._DbObj = None
        self._id_field = None
        self._order_field = None

    @staticmethod
    def get_session():
        return connection.get_session()

    def list_all(self):
        query = _Query(self)
        query.add_order_condition()
        for entity in query:
            yield entity

    def get_by_id(self, entity_id):
        query = _Query(self)
        query.add_id_condition(entity_id)
        return query.one()

    def create(self):
        session = connection.get_session()
        entity = self._DbObj()
        session.add(entity)
        return entity

    def delete_by_id(self, entity_id):
        """
        Delete an entity from the DB whose ID is given
        :param entity_id:
        :return: True if an entity was found and deleted, false if no such
         entity exists
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        session = connection.get_session()
        session.delete(entity)
        return True


class _SystemChildEntityDao(_BaseEntityDao):

    def list_all_in_system(self, system_id):
        query = _Query(self)
        query.add_system_condition(system_id)
        query.add_order_condition()
        for entity in query:
            yield entity

    def get_in_system_by_id(self, system_id, entity_id):
        query = _Query(self)
        query.add_id_condition(entity_id)
        query.add_system_condition(system_id)
        return query.one()


def _dao_factory(schema_entity, id_field, order_field=None, base_dao=_BaseEntityDao):

    # @singleton
    class NewDao(base_dao):
        def __init__(self):
            super().__init__()
            self._DbObj = schema_entity
            self._id_field = getattr(schema_entity, id_field)
            if order_field is not None:
                self._order_field = getattr(schema_entity, order_field)

    return NewDao


StopDao = _dao_factory(schema_entity=models.Stop,
                       id_field='stop_id',
                       order_field='name',
                       base_dao=_SystemChildEntityDao)

_RouteDao = _dao_factory(schema_entity=models.Route,
                         id_field='route_id',
                         order_field='route_id',
                         base_dao=_SystemChildEntityDao)

SystemDao = _dao_factory(schema_entity=models.System,
                         id_field='system_id',
                         order_field='system_id',
                         base_dao=_BaseEntityDao)

FeedDao = _dao_factory(schema_entity=models.Feed,
                       id_field='feed_id',
                       order_field='feed_id',
                       base_dao=_SystemChildEntityDao)

FeedUpdateDao = _dao_factory(schema_entity=models.FeedUpdate,
                             id_field='id',
                             order_field='id',
                             base_dao=_BaseEntityDao)

_StopEventDao = _dao_factory(schema_entity=models.StopEvent,
                             id_field='id',
                             order_field='id',
                             base_dao=_BaseEntityDao)

_TripDao = _dao_factory(schema_entity=models.Trip,
                        id_field='id',
                        order_field='id',
                        base_dao=_BaseEntityDao)


class TripDao(_TripDao):
    @staticmethod
    def list_all_in_route(system_id, route_id):
        session = connection.get_session()
        query = session.query(models.Trip) \
            .join(models.Route, models.Route.id == models.Trip.route_pri_key) \
            .filter(models.Route.system_id == system_id) \
            .filter(models.Route.route_id == route_id)
        for row in query:
            yield row

    @staticmethod
    def get_in_route_by_id(system_id, route_id, trip_id):
        session = connection.get_session()
        query = session.query(models.Trip)\
            .join(models.Route, models.Route.id == models.Trip.route_pri_key)\
            .filter(models.Route.system_id == system_id)\
            .filter(models.Route.route_id == route_id)\
            .filter(models.Trip.trip_id == trip_id)
        return query.one()



class RouteDao(_RouteDao):
    @staticmethod
    def get_active_stop_ids(route_pri_key):
        session = connection.get_session()
        query = session.query(models.Stop.stop_id)\
            .join(models.StopEvent, models.Stop.id == models.StopEvent.stop_pri_key)\
            .join(models.Trip, models.Trip.id == models.StopEvent.trip_pri_key)\
            .join(models.Route, models.Trip.route_pri_key == models.Route.id)\
            .filter(models.Route.id == route_pri_key)
        for row in query:
            yield row[0]


class StopEventDao(_StopEventDao):

    def get_by_stop_pri_key(self, stop_pri_key):
        session = connection.get_session()
        query = session.query(self._DbObj)\
            .filter(self._DbObj.stop_pri_key==stop_pri_key) \
            .filter(self._DbObj.future == True)\
            .order_by(self._DbObj.departure_time)\
            .order_by(self._DbObj.arrival_time)
        for row in query:
            yield row
