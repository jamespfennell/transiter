from transiter.database import connection
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

    class NewDao(base_dao):
        def __init__(self):
            super().__init__()
            self._DbObj = schema_entity
            self._id_field = getattr(schema_entity, id_field)
            if order_field is not None:
                self._order_field = getattr(schema_entity, order_field)

    return NewDao
