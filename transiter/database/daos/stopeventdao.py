from transiter.database.daos import daofactory
from transiter.database import models


_BaseStopEventDao = daofactory._dao_factory(
    schema_entity=models.StopTimeUpdate,
    id_field='pk',
    order_field='pk',
    base_dao=daofactory._BaseEntityDao)

# TODO This should be in the stop dao
class _StopEventDao(_BaseStopEventDao):

    def get_by_stop_pri_key(self, stop_pk):
        session = self.get_session()
        query = session.query(self._DbObj)\
            .filter(self._DbObj.stop_pk==stop_pk) \
            .filter(self._DbObj.future == True)\
            .order_by(self._DbObj.departure_time)\
            .order_by(self._DbObj.arrival_time)
        for row in query:
            yield row

    def get_by_stop_pks(self, stop_pks):
        session = self.get_session()
        query = session.query(self._DbObj)\
            .filter(self._DbObj.stop_pk.in_(stop_pks)) \
            .filter(self._DbObj.future == True)\
            .order_by(self._DbObj.departure_time)\
            .order_by(self._DbObj.arrival_time)
        for row in query:
            yield row


stop_event_dao = _StopEventDao()
