from transiter.database.daos import daofactory
from transiter.database import models


_BaseFeedDao = daofactory._dao_factory(
    schema_entity=models.Feed,
    id_field='feed_id',
    order_field='feed_id',
    base_dao=daofactory._SystemChildEntityDao)


class _FeedDao(_BaseFeedDao):

    def get_last_successful_update(self, feed_pri_key):
        session = self.get_session()
        query = session.query(models.FeedUpdate)\
            .filter(models.FeedUpdate.feed_pri_key==feed_pri_key)\
            .order_by(models.FeedUpdate.last_action_time.desc())\
            .filter(models.FeedUpdate.status == 'SUCCESS_UPDATED')\
            .limit(1)

        return query.first()


feed_dao = _FeedDao()