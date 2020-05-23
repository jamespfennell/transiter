import collections
import datetime
import typing

from sqlalchemy import sql
from sqlalchemy.orm import joinedload

from transiter.db import dbconnection, models


def get_route_pk_to_active_alerts(
    route_pks, current_time=None, load_messages=False,
) -> typing.Dict[
    int, typing.List[typing.Tuple[models.AlertActivePeriod, models.Alert]]
]:
    return _get_entity_pk_to_active_alerts(
        models.Route, models.Alert.routes, route_pks, current_time, load_messages
    )


def get_stop_pk_to_active_alerts(
    stop_pks, current_time=None, load_messages=False,
) -> typing.Dict[
    int, typing.List[typing.Tuple[models.AlertActivePeriod, models.Alert]]
]:
    return _get_entity_pk_to_active_alerts(
        models.Stop, models.Alert.stops, stop_pks, current_time, load_messages
    )


def get_agency_pk_to_active_alerts(
    agency_pks, current_time=None, load_messages=False,
) -> typing.Dict[
    int, typing.List[typing.Tuple[models.AlertActivePeriod, models.Alert]]
]:
    return _get_entity_pk_to_active_alerts(
        models.Agency, models.Alert.agencies, agency_pks, current_time, load_messages
    )


def get_trip_pk_to_active_alerts(
    trip_pks, current_time=None, load_messages=False,
) -> typing.Dict[
    int, typing.List[typing.Tuple[models.AlertActivePeriod, models.Alert]]
]:
    return _get_entity_pk_to_active_alerts(
        models.Trip, models.Alert.trips, trip_pks, current_time, load_messages
    )


def _get_entity_pk_to_active_alerts(
    entity_type, entity_relationship, pks, current_time, load_messages
):
    pks = list(pks)
    if len(pks) == 0:
        return {}
    if current_time is None:
        current_time = datetime.datetime.utcnow()
    query = (
        dbconnection.get_session()
        .query(entity_type.pk, models.AlertActivePeriod, models.Alert)
        .filter(models.AlertActivePeriod.alert_pk == models.Alert.pk)
        .filter(
            sql.or_(
                models.AlertActivePeriod.starts_at <= current_time,
                models.AlertActivePeriod.starts_at.is_(None),
            )
        )
        .filter(
            sql.or_(
                models.AlertActivePeriod.ends_at >= current_time,
                models.AlertActivePeriod.ends_at.is_(None),
            )
        )
        .order_by(models.AlertActivePeriod.starts_at)
        .join(entity_relationship)
        .filter(entity_type.pk.in_(pks))
    )
    if load_messages:
        query = query.options(joinedload(models.Alert.messages))
    pk_to_alert_pks = collections.defaultdict(set)
    pk_to_tuple = {pk: [] for pk in pks}
    for pk, active_period, alert in query.all():
        if alert.pk in pk_to_alert_pks[pk]:
            continue
        pk_to_alert_pks[pk].add(alert.pk)
        pk_to_tuple[pk].append((active_period, alert))
    return pk_to_tuple
