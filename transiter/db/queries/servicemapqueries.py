from typing import Dict, Iterable

import sqlalchemy.sql.expression as sql
from sqlalchemy.orm import selectinload

from transiter.db import dbconnection, models


def list_groups_and_maps_for_stops_in_route(route_pk):
    """
    This function is used to get the service maps for a route.

    It returns a list of tuples (service map group, service map) for each
    service map group having use_for_stops_in_route equal True.

    :param route_pk: the route's PK
    :return: the list described above
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.ServiceMapGroup, models.ServiceMap)
        .join(models.System, models.System.pk == models.ServiceMapGroup.system_pk)
        .join(models.Route, models.Route.system_pk == models.System.pk)
        .outerjoin(
            models.ServiceMap,
            sql.and_(
                models.ServiceMap.route_pk == models.Route.pk,
                models.ServiceMap.group_pk == models.ServiceMapGroup.pk,
            ),
        )
        .filter(models.ServiceMapGroup.use_for_stops_in_route)
        .filter(models.Route.pk == route_pk)
        .options(selectinload(models.ServiceMap.vertices))
        .options(selectinload(models.ServiceMap.vertices, models.ServiceMapVertex.stop))
    )
    return [(group, map_) for (group, map_) in query]


def get_stop_pk_to_group_id_to_routes_map(
    stop_pks,
) -> Dict[int, Dict[str, Iterable[models.Route]]]:
    """
    This function is used to get service map information for stops; namely,
    which routes call at the stop based on the service maps.

    Get a map whose key is a stop's PK and whose the value is another map.
    This second map has a key for every service map group having
    use_for_routes_at_stop equal to True. The value of this map is the list of
    routes that contain the stop in the relevant service map.

    :param stop_pks: stop PKs to build the map for
    :return: the monster map described above
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.Stop.pk, models.ServiceMapGroup.id, models.Route)
        .join(models.System, models.System.pk == models.Stop.system_pk)
        .join(
            models.ServiceMapGroup,
            sql.and_(
                models.ServiceMapGroup.system_pk == models.System.pk,
                models.ServiceMapGroup.use_for_routes_at_stop,
            ),
        )
        .outerjoin(
            models.ServiceMap,
            sql.and_(
                models.ServiceMap.group_pk == models.ServiceMapGroup.pk,
                models.ServiceMap.pk.in_(
                    session.query(models.ServiceMapVertex.map_pk).filter(
                        models.ServiceMapVertex.stop_pk == models.Stop.pk
                    )
                ),
            ),
        )
        .outerjoin(models.Route, models.Route.pk == models.ServiceMap.route_pk)
        .filter(models.Stop.pk.in_(stop_pks))
    )
    response = {stop_pk: {} for stop_pk in stop_pks}
    for stop_pk, group_id, route in query:
        if group_id not in response[stop_pk]:
            response[stop_pk][group_id] = []
        if route is not None:
            response[stop_pk][group_id].append(route)
    return response
