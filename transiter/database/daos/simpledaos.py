from transiter.database.daos import daofactory
from transiter.database import models


_DirectionNameDao = daofactory._dao_factory(
    schema_entity=models.DirectionName,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)

direction_name_dao = _DirectionNameDao()


_StationDao = daofactory._dao_factory(
    schema_entity=models.Station,
    id_field='id',
    order_field='name',
    base_dao=daofactory._SystemChildEntityDao)

station_dao = _StationDao()


_BaseStopDao = daofactory._dao_factory(
    schema_entity=models.Stop,
    id_field='stop_id',
    order_field='name',
    base_dao=daofactory._SystemChildEntityDao)


class _StopDao(_BaseStopDao):

    def get_stop_id_alias_to_stop_id_map(self, system_id, stop_id_aliases):
        session = self.get_session()
        query = (
            session.query(models.StopAlias.stop_id_alias, models.StopAlias.stop_id)
            .filter(models.StopAlias.stop_id_alias.in_(stop_id_aliases))
            .filter(models.StopAlias.system_id == system_id)
            .all()
        )
        result = {stop_id_alias: None for stop_id_alias in stop_id_aliases}
        for row in query:
            result[row[0]] = row[1]
        return result

    # TODO: this replicates the route map. Make a common method that they both call
    # This works for any system child entity
    def get_id_to_pk_map(self, system_id, ids):
        id_to_pk = {id_: None for id_ in ids}
        session = self.get_session()
        query = (
            session.query(models.Stop.stop_id, models.Stop.id)
            .filter(models.Stop.stop_id.in_(ids))
            .filter(models.Stop.system_id == system_id)
            .all()
        )
        for (id_, pk) in query:
            id_to_pk[id_] = pk
        return id_to_pk
    pass


stop_dao = _StopDao()

