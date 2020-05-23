import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import alertqueries, genericqueries, systemqueries
from transiter.services import agencyservice, views

SYSTEM_ID = "1"
AGENCY_ONE_ID = "3"
AGENCY_ONE_NAME = "agency_1"
AGENCY_TWO_ID = "5"
AGENCY_TWO_NAME = "agency_2"
ROUTE_ID = "7"
ROUTE_COLOR = "8"


def test_list_all_in_system__system_not_found(monkeypatch):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        agencyservice.list_all_in_system(SYSTEM_ID)


def test_list_all_in_system(monkeypatch):
    system = models.System(id=SYSTEM_ID)
    agency_1 = models.Agency(system=system, id=AGENCY_ONE_ID, name=AGENCY_ONE_NAME)
    agency_2 = models.Agency(system=system, id=AGENCY_TWO_ID, name=AGENCY_TWO_NAME)

    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: system)
    monkeypatch.setattr(
        genericqueries, "list_in_system", lambda *args: [agency_1, agency_2]
    )
    monkeypatch.setattr(
        alertqueries, "get_agency_pk_to_active_alerts", lambda *args, **kwargs: {}
    )

    expected = [
        views.Agency(
            id=AGENCY_ONE_ID, _system_id=SYSTEM_ID, name=AGENCY_ONE_NAME, alerts=[]
        ),
        views.Agency(
            id=AGENCY_TWO_ID, _system_id=SYSTEM_ID, name=AGENCY_TWO_NAME, alerts=[]
        ),
    ]

    actual = agencyservice.list_all_in_system(SYSTEM_ID)

    assert actual == expected


def test_get_in_system_by_id__route_not_found(monkeypatch):
    monkeypatch.setattr(genericqueries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        agencyservice.get_in_system_by_id(SYSTEM_ID, AGENCY_ONE_ID)


def test_get_in_system_by_id(monkeypatch):
    system = models.System(id=SYSTEM_ID)
    route = models.Route(id=ROUTE_ID, color=ROUTE_COLOR, system=system)
    agency_1 = models.Agency(
        system=system, id=AGENCY_ONE_ID, name=AGENCY_ONE_NAME, routes=[route], alerts=[]
    )

    monkeypatch.setattr(genericqueries, "get_in_system_by_id", lambda *args: agency_1)
    monkeypatch.setattr(
        alertqueries, "get_agency_pk_to_active_alerts", lambda *args, **kwargs: {}
    )

    expected = views.AgencyLarge(
        id=AGENCY_ONE_ID,
        name=AGENCY_ONE_NAME,
        timezone=None,
        url=None,
        routes=[views.Route(id=ROUTE_ID, color=ROUTE_COLOR, _system_id=SYSTEM_ID)],
        alerts=[],
    )

    actual = agencyservice.get_in_system_by_id(SYSTEM_ID, AGENCY_ONE_ID)

    assert expected == actual
