from transiter.database.daos import daofactory
from transiter.database import models


_DirectionNameDao = daofactory._dao_factory(
    schema_entity=models.DirectionName,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)

direction_name_dao = _DirectionNameDao()


_FeedUpdateDao = daofactory._dao_factory(
    schema_entity=models.FeedUpdate,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)

feed_update_dao = _FeedUpdateDao()


_StationDao = daofactory._dao_factory(
    schema_entity=models.Station,
    id_field='id',
    order_field='name',
    base_dao=daofactory._SystemChildEntityDao)

station_dao = _StationDao()


_StopDao = daofactory._dao_factory(
    schema_entity=models.Stop,
    id_field='stop_id',
    order_field='name',
    base_dao=daofactory._SystemChildEntityDao)

stop_dao = _StopDao()
