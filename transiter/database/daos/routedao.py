from transiter.database.daos import daofactory
from transiter import models

_BaseRouteDao = daofactory._dao_factory(
    schema_entity=models.Route,
    id_field='id',
    order_field='id',
    base_dao=daofactory._SystemChildEntityDao)


class RouteDao(_BaseRouteDao):

    def get_id_to_pk_map(self, system_id, route_ids):
        id_to_pk = {route_id: None for route_id in route_ids}
        session = self.get_session()
        query = (
            session.query(models.Route.id, models.Route.pk)
            .filter(models.Route.id.in_(route_ids))
            .all()
        )
        for (id_, pk) in query:
            id_to_pk[id_] = pk
        return id_to_pk


route_dao = RouteDao()
