from . import dbschema
from . import dbconnection
from . import dbexceptions

from sqlalchemy.orm.exc import NoResultFound




class _BaseDao:

    def __init__(self):
        self._DbObj = None
        self._id_field = None
        self._order_field = None
        self.system_id = None

    @staticmethod
    def get_session():
        return dbconnection.get_session()

    def list(self):
        session = dbconnection.get_session()
        query = session.query(self._DbObj)
        if self._order_field is not None:
            query = query.order_by(self._order_field)
        for row in query:
            yield row

    def get_by_id(self, entity_id, system_id=None):
        if system_id is None:
            system_id = self.system_id
        session = dbconnection.get_session()
        query = session.query(self._DbObj).filter(self._id_field==entity_id)
        if system_id is not None:
            query = query.filter(self._DbObj.system_id==system_id)
        try:
            return query.one()
        except NoResultFound:
            return None
        """
        raise dbexceptions.IdNotFoundError(
            'No entry exists in table "{}" with {}={}'.format(
                self._DbObj.__tablename__,
                self._id_field.key,
                entity_id
            ))
        """

    def create(self):
        session = dbconnection.get_session()
        entity = self._DbObj()
        session.add(entity)
        return entity

    def delete(self, entity_id):
        """
        Delete an entity from the DB whose ID is given
        :param entity_id:
        :return: True if an entity was found and deleted, false if no such
         entity exists
        """
        session = dbconnection.get_session()
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        session.delete(entity)
        return True


def _dao_factory(schema_entity, id_field, order_field=None):
    # @singleton
    class NewDao(_BaseDao):
        def __init__(self):
            super().__init__()
            self._DbObj = schema_entity
            self._id_field = getattr(schema_entity, id_field)
            if order_field is not None:
                self._order_field = getattr(schema_entity, order_field)

    return NewDao


StopDao = _dao_factory(dbschema.Stop, 'stop_id', 'name')
RouteDao = _dao_factory(dbschema.Route, 'route_id', 'route_id')
SystemDao = _dao_factory(dbschema.System, 'system_id', 'system_id')
FeedDao = _dao_factory(dbschema.Feed, 'feed_id', 'feed_id')
FeedUpdateDao = _dao_factory(dbschema.FeedUpdate, 'id', 'id')

_StopEventDao = _dao_factory(dbschema.StopEvent, 'id')
class StopEventDao(_StopEventDao):

    def get_by_stop_pri_key(self, stop_pri_key):
        session = dbconnection.get_session()
        query = session.query(self._DbObj).filter(self._DbObj.stop_pri_key==stop_pri_key)
        for row in query:
            yield row
