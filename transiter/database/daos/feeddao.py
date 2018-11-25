from transiter.database.daos import daofactory
from transiter import models

_BaseFeedDao = daofactory._dao_factory(
    schema_entity=models.Feed,
    id_field='id',
    order_field='id',
    base_dao=daofactory._SystemChildEntityDao)


# TODO: why are these DAOs different?


class _FeedDao(_BaseFeedDao):

    def get_last_successful_update(self, feed_pri_key):
        session = self.get_session()
        query = session.query(models.FeedUpdate)\
            .filter(models.FeedUpdate.feed_pk == feed_pri_key)\
            .order_by(models.FeedUpdate.last_action_time.desc())\
            .filter(models.FeedUpdate.status == 'SUCCESS_UPDATED')\
            .limit(1)

        return query.first()


feed_dao = _FeedDao()


_BaseFeedUpdateDao = daofactory._dao_factory(
    schema_entity=models.FeedUpdate,
    id_field='pk',
    order_field='pk',
    base_dao=daofactory._BaseEntityDao)


class _FeedUpdateDao(_BaseFeedUpdateDao):
    # TODO input should be a feed id
    # TODO is this needed? Can a relationship be used instead?
    def list_updates_in_feed(self, feed):
        session = self.get_session()
        query = session.query(models.FeedUpdate).filter(
            models.FeedUpdate.feed_pk == feed.pk
        ).order_by(models.FeedUpdate.last_action_time.desc())
        for feed_update in query:
            yield feed_update


feed_update_dao = _FeedUpdateDao()
