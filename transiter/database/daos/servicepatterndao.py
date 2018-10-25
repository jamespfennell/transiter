from transiter.database.daos import daofactory
from transiter.database import models


_BaseServicePatternDao = daofactory._dao_factory(
    schema_entity=models.ServicePattern,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)


class _ServicePatternDao(_BaseServicePatternDao):

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

    def get_default_trips_at_stops(self, stop_ids):
        response = {stop_id: [] for stop_id in stop_ids}
        query = """
        SELECT stops.stop_id, routes.route_id
        FROM stops
        INNER JOIN service_pattern_vertices
            ON stops.id = service_pattern_vertices.stop_pri_key
        INNER JOIN service_patterns
            ON service_pattern_vertices.service_pattern_pri_key = service_patterns.id
        INNER JOIN routes
            ON routes.default_service_pattern_pri_key = service_patterns.id
        WHERE stops.stop_id IN :stop_ids;
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
