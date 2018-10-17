from transiter.database.daos import daofactory
from transiter.database import models


_BaseRouteDao = daofactory._dao_factory(
    schema_entity=models.Route,
    id_field='route_id',
    order_field='route_id',
    base_dao=daofactory._SystemChildEntityDao)


class RouteDao(_BaseRouteDao):
    def get_active_stop_ids(self, route_pri_key):
        session = self.get_session()
        query = session.query(models.Stop.stop_id)\
            .join(models.StopEvent, models.Stop.id == models.StopEvent.stop_pri_key)\
            .join(models.Trip, models.Trip.id == models.StopEvent.trip_pri_key)\
            .join(models.Route, models.Trip.route_pri_key == models.Route.id)\
            .filter(models.Route.id == route_pri_key)
        for row in query:
            yield row[0]


route_dao = RouteDao()
