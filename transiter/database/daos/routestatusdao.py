from transiter.database.daos import daofactory
from transiter.database import models


class _RouteStatusDao(daofactory._BaseEntityDao):

    def get_all_in_system(self, system_id):
        session = self.get_session()
        query = session.query(models.RouteStatus)\
            .join(models.Route, models.RouteStatus.routes)\
            .join(models.System, models.Route.system)\
            .filter(models.System.system_id == system_id)
        for row in query:
            yield row


route_status_dao = _RouteStatusDao()
