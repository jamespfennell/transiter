import typing

from transiter import exceptions, models
from transiter.data import dbconnection
from transiter.data.dams import systemdam, genericqueries
from transiter.services import views


@dbconnection.unit_of_work
def list_all_in_system(system_id) -> typing.List[views.Agency]:
    system = systemdam.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    return list(
        map(
            views.Agency.from_model,
            genericqueries.list_all_in_system(models.Agency, system_id),
        )
    )


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, agency_id) -> views.AgencyLarge:
    agency = genericqueries.get_in_system_by_id(models.Agency, system_id, agency_id)
    if agency is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=agency_id
        )
    response = views.AgencyLarge.from_model(agency)
    response.alerts = list(map(views.AlertLarge.from_model, agency.alerts))
    response.routes = list(map(views.Route.from_model, agency.routes))
    return response
