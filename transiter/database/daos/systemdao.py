from transiter.database.daos import daofactory
from transiter import models
from sqlalchemy import func

_BaseSystemDao = daofactory._dao_factory(
    schema_entity=models.System,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)


class _SystemDao(_BaseSystemDao):

    def _count_child_entity_in_system(self, system_id, Model):
        session = self.get_session()
        query = session.query(func.count(Model.pk)) \
            .filter(Model.system_id == system_id)
        return query.one()[0]

    def count_stations_in_system(self, system_id):
        return 0

    def count_stops_in_system(cls, system_id):
        return cls._count_child_entity_in_system(system_id, models.Stop)

    def count_routes_in_system(cls, system_id):
        return cls._count_child_entity_in_system(system_id, models.Route)

    def count_feeds_in_system(cls, system_id):
        return cls._count_child_entity_in_system(system_id, models.Feed)


system_dao = _SystemDao()