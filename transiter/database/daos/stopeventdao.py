from transiter.database.daos import daofactory
from transiter.database import models


_BaseStopEventDao = daofactory._dao_factory(
    schema_entity=models.StopEvent,
    id_field='id',
    order_field='id',
    base_dao=daofactory._BaseEntityDao)


class _StopEventDao(_BaseStopEventDao):

    def get_by_stop_pri_key(self, stop_pri_key):
        session = self.get_session()
        query = session.query(self._DbObj)\
            .filter(self._DbObj.stop_pri_key==stop_pri_key) \
            .filter(self._DbObj.future == True)\
            .order_by(self._DbObj.departure_time)\
            .order_by(self._DbObj.arrival_time)
        for row in query:
            yield row


stop_event_dao = _StopEventDao()
