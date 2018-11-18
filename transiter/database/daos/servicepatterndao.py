from transiter.database.daos import daofactory
from transiter.database import models


_BaseServicePatternDao = daofactory._dao_factory(
    schema_entity=models.ServicePattern,
    id_field='pk',
    order_field='pk',
    base_dao=daofactory._BaseEntityDao)

# TODO: is a service pattern dao really needed?

class _ServicePatternDao(_BaseServicePatternDao):

    """
    def create_vertex(self):
        vertex = models.ServicePatternVertex()
        session = self.get_session()
        session.add(vertex)
        return vertex

    def temp_create_route_list_entry(self):

        route_list_entry = models.RouteListEntry()
        session = self.get_session()
        session.add(route_list_entry)
        return route_list_entry
    """
    # TODO this should be either by stop_pk or also include system
    # TODO should this return route objects? Question of efficiency
    # TODO can we by default only return some columns of the route objects?
    # I.e., load other lazily, and then just get enough to construct the href
    def get_default_trips_at_stops(self, stop_ids):
        response = {stop_id: [] for stop_id in stop_ids}
        query = """
        SELECT stop.id, route.id
        FROM stop
        INNER JOIN service_pattern_vertex
            ON stop.pk = service_pattern_vertex.stop_pk
        INNER JOIN service_pattern
            ON service_pattern_vertex.service_pattern_pk = service_pattern.pk
        INNER JOIN route
            ON route.regular_service_pattern_pk = service_pattern.pk
        WHERE stop.id IN :stop_ids;
        """
        session = self.get_session()
        result = session.execute(query, {'stop_ids': tuple(stop_ids)})

        for (stop_id, route_id) in result:
            response[stop_id].append(route_id)

        return response

"""
def get_by_stop_pri_key(self, stop_pri_key):
    session = self.get_session()
    query = session.query(self._DbObj)\
        .filter(self._DbObj.stop_pri_key==stop_pri_key) \
        .filter(self._DbObj.future == True)\
        .order_by(self._DbObj.departure_time)\
        .order_by(self._DbObj.arrival_time)
    for row in query:
        yield row
"""


service_pattern_dao = _ServicePatternDao()
