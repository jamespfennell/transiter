import typing

from transiter import exceptions
from transiter.db import dbconnection, models
from transiter.db.queries import genericqueries, systemqueries
from transiter.services import views, helpers


@dbconnection.unit_of_work
def list_all_in_system(
    system_id, alerts_detail: views.AlertsDetail = None
) -> typing.List[views.Agency]:
    system = systemqueries.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    agencies = genericqueries.list_in_system(models.Agency, system_id)
    response = list(map(views.Agency.from_model, agencies))
    helpers.add_alerts_to_views(
        response, agencies, alerts_detail or views.AlertsDetail.CAUSE_AND_EFFECT
    )
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(
    system_id, agency_id, alerts_detail: views.AlertsDetail = None
) -> views.AgencyLarge:
    agency = genericqueries.get_in_system_by_id(models.Agency, system_id, agency_id)
    if agency is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=agency_id
        )
    response = views.AgencyLarge.from_model(agency)
    helpers.add_alerts_to_views(
        [response], [agency], alerts_detail or views.AlertsDetail.MESSAGES
    )
    response.routes = list(map(views.Route.from_model, agency.routes))
    return response
