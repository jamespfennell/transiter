from transiter.database.daos import daofactory
from transiter import models

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
    # TODO turn this into a sql alchemy query and load route models containing
    # only the route_id and system_id as these are the only ones needed for
    # linksutil
    # TODO can we by default only return some columns of the route objects?
    # I.e., load other lazily, and then just get enough to construct the href
    # https://docs.sqlalchemy.org/en/latest/orm/loading_columns.html
    def get_default_trips_at_stops(self, stop_pks):
        response = {stop_pk: [] for stop_pk in stop_pks}
        query = """
        SELECT stop.pk, route.id
        FROM stop
        INNER JOIN service_pattern_vertex
            ON stop.pk = service_pattern_vertex.stop_pk
        INNER JOIN service_pattern
            ON service_pattern_vertex.service_pattern_pk = service_pattern.pk
        INNER JOIN route
            ON route.regular_service_pattern_pk = service_pattern.pk
        WHERE stop.pk IN :stop_pks;
        """
        session = self.get_session()
        result = session.execute(query, {'stop_pks': tuple(stop_pks)})

        for (stop_pk, route_id) in result:
            response[stop_pk].append(route_id)
        print(response)
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
