from transiter.database.daos import daofactory
from transiter import models

_BaseRouteDao = daofactory._dao_factory(
    schema_entity=models.Route,
    id_field='id',
    order_field='id',
    base_dao=daofactory._SystemChildEntityDao)


class RouteDao(_BaseRouteDao):

    def get_id_to_pk_map(self, system_id, route_ids):
        # TODO: need to input the transit system
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

    def get_active_stop_ids(self, route_pk):
        session = self.get_session()
        query = (
            session.query(models.Stop.id)
            .distinct()
            .join(models.StopTimeUpdate, models.Stop.pk == models.StopTimeUpdate.stop_pk)
            .join(models.Trip, models.Trip.pk == models.StopTimeUpdate.trip_pk)
            .join(models.Route, models.Trip.route_pk == models.Route.pk)
            .filter(models.Route.pk == route_pk)
        )
        for row in query:
            yield row[0]

    def get_terminus_data(self, route_pri_key):

        session = self.get_session()
        query = """
        SELECT
            MIN(stop_time_update.arrival_time) as first_arrival_time,
            MAX(stop_time_update.arrival_time) as last_arrival_time,
            COUNT(*) as number_of_trips,
            stop_time_update.stop_pk
        FROM route
        INNER JOIN trip
            ON trip.route_pk = route.pk
        INNER JOIN stop_time_update
            ON stop_time_update.pk = (
                SELECT pk
                FROM stop_time_update
                WHERE trip_pk = trip.pk
                AND future = true
                ORDER BY arrival_time DESC
                LIMIT 1
            )
        WHERE route.pk = :route_pri_key
        AND trip.current_status != 'SCHEDULED'
        GROUP BY stop_time_update.stop_pk;
        """
        result = session.execute(query, {'route_pri_key': route_pri_key})
        for row in result:
            yield row




route_dao = RouteDao()
