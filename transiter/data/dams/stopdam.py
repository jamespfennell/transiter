from transiter import models
from transiter.data import database
from transiter.data.dams import genericqueries


def list_all_in_system(system_id):
    yield from genericqueries.list_all_in_system(
        models.Stop, system_id, models.Stop.id
    )


def get_in_system_by_id(system_id, stop_id):
    return genericqueries.get_in_system_by_id(
        models.Stop, system_id, stop_id
    )


def get_id_to_pk_map_in_system(system_id, stop_ids=None):
    return genericqueries.get_id_to_pk_map(
        models.Stop, system_id, stop_ids
    )


def list_stop_time_updates_at_stops(stop_pks):
    # TODO: is the order_by here problematic?
    session = database.get_session()
    query = (
        session.query(models.StopTimeUpdate)
        .filter(models.StopTimeUpdate.stop_pk.in_(stop_pks))
        .filter(models.StopTimeUpdate.future == True)
        .order_by(models.StopTimeUpdate.departure_time)
        .order_by(models.StopTimeUpdate.arrival_time)
    )
    for row in query:
        yield row


def get_stop_pk_to_station_pk_map_in_system(system_id):
    session = database.get_session()
    query = (
        session.query(models.Stop.pk, models.Stop.parent_stop_pk, models.Stop.is_station)
        .filter(models.Stop.system_id == system_id)
    )
    stop_pk_to_station_pk = {}
    for stop_pk, parent_stop_pk, is_station in query:
        if is_station:
            stop_pk_to_station_pk[stop_pk] = stop_pk
        else:
            stop_pk_to_station_pk[stop_pk] = parent_stop_pk
    return stop_pk_to_station_pk
