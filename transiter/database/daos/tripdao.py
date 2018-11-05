from transiter.database.daos import daofactory
from transiter.database import models

from sqlalchemy.orm.exc import NoResultFound

_BaseTripDao = daofactory._dao_factory(
    schema_entity=models.Trip,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)


class _TripDao(_BaseTripDao):

    def list_all_in_routes(self, system_id, route_ids):
        session = self.get_session()
        query = session.query(models.Trip) \
            .join(models.Route, models.Route.id == models.Trip.route_pri_key) \
            .filter(models.Route.system_id == system_id) \
            .filter(models.Route.route_id.in_(route_ids))
        for row in query:
            yield row

    # TODO: make this call the one above
    def list_all_in_route(self, system_id, route_id):
        session = self.get_session()
        query = session.query(models.Trip) \
            .join(models.Route, models.Route.id == models.Trip.route_pri_key) \
            .filter(models.Route.system_id == system_id) \
            .filter(models.Route.route_id == route_id)
        for row in query:
            yield row

    def get_in_route_by_id(self, system_id, route_id, trip_id):
        session = self.get_session()
        query = session.query(models.Trip)\
            .join(models.Route, models.Route.id == models.Trip.route_pri_key)\
            .filter(models.Route.system_id == system_id)\
            .filter(models.Route.route_id == route_id)\
            .filter(models.Trip.trip_id == trip_id)
        try:
            return query.one()
        except NoResultFound:
            return None

    def get_trip_pk_to_future_stop_events_map(self, trip_pks):
        session = self.get_session()
        query = (
            session.query(models.StopEvent)
            .filter(models.StopEvent.trip_pri_key.in_(trip_pks))
            .filter(models.StopEvent.future == True)
            .order_by(models.StopEvent.sequence_index)
            .all()
        )
        result = {trip_pk: [] for trip_pk in trip_pks}
        for row in query:
            result[row.trip_pri_key].append(row)
        return result



trip_dao = _TripDao()
