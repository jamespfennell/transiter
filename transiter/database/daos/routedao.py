from transiter.database.daos import daofactory
from transiter.database import models


_BaseRouteDao = daofactory._dao_factory(
    schema_entity=models.Route,
    id_field='route_id',
    order_field='route_id',
    base_dao=daofactory._SystemChildEntityDao)


class RouteDao(_BaseRouteDao):

    def get_id_to_pk_map(self, system_id, route_ids):
        # TODO: need to input the transit system
        id_to_pk = {route_id: None for route_id in route_ids}
        session = self.get_session()
        query = (
            session.query(models.Route.route_id, models.Route.id)
            .filter(models.Route.route_id.in_(route_ids))
            .all()
        )
        for (id_, pk) in query:
            id_to_pk[id_] = pk
        return id_to_pk

    def get_active_stop_ids(self, route_pri_key):
        session = self.get_session()
        query = (
            session.query(models.Stop.stop_id)
            .distinct()
            .join(models.StopEvent, models.Stop.id == models.StopEvent.stop_pri_key)
            .join(models.Trip, models.Trip.id == models.StopEvent.trip_pri_key)
            .join(models.Route, models.Trip.route_pri_key == models.Route.id)
            .filter(models.Route.id == route_pri_key)
        )
        for row in query:
            yield row[0]

    def get_terminus_data(self, route_pri_key):

        session = self.get_session()
        query = """
        SELECT
            MIN(stop_events.arrival_time) as first_arrival_time,
            MAX(stop_events.arrival_time) as last_arrival_time,
            COUNT(*) as number_of_trips,
            stop_events.stop_pri_key
        FROM routes
        INNER JOIN trips
            ON trips.route_pri_key = routes.id
        INNER JOIN stop_events
            ON stop_events.id = (
                SELECT id
                FROM stop_events
                WHERE trip_pri_key = trips.id
                AND future = true
                ORDER BY arrival_time DESC
                LIMIT 1
            )
        WHERE routes.id = :route_pri_key
        AND trips.current_status != 'SCHEDULED'
        GROUP BY stop_events.stop_pri_key;
        """
        result = session.execute(query, {'route_pri_key': route_pri_key})
        for row in result:
            yield row




route_dao = RouteDao()
