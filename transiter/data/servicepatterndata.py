from transiter.data import database
from transiter import models


def get_default_routes_at_stops_map(stop_pks):
    session = database.get_session()
    query = (
        session.query(models.Stop.pk, models.Route)
        .join(models.ServicePatternVertex,
              models.ServicePatternVertex.stop_pk == models.Stop.pk)
        .join(models.Route,
              models.Route.regular_service_pattern_pk == models.ServicePatternVertex.service_pattern_pk)
        .filter(models.Stop.pk.in_(stop_pks))
    )

    response = {stop_pk: [] for stop_pk in stop_pks}
    for (stop_pk, route) in query:
        response[stop_pk].append(route)
    return response
