from transiter.data import database
from transiter.data.dams import genericqueries
from transiter import models


def list_all_autoupdating():
    session = database.get_session()
    query = (
        session.query(models.Feed)
        .filter(models.Feed.auto_updater_enabled)
    )
    for row in query:
        yield row


def list_all_in_system(system_id):
    yield from genericqueries.list_all_in_system(
        models.Feed, system_id, models.Feed.id
    )


def get_in_system_by_id(system_id, feed_id):
    return genericqueries.get_in_system_by_id(
        models.Feed, system_id, feed_id
    )


def get_last_successful_update(feed_pri_key):
    session = database.get_session()
    query = session.query(models.FeedUpdate) \
        .filter(models.FeedUpdate.feed_pk == feed_pri_key) \
        .order_by(models.FeedUpdate.last_action_time.desc()) \
        .filter(models.FeedUpdate.status == 'SUCCESS') \
        .limit(1)

    return query.first()


def list_updates_in_feed(feed):
    session = database.get_session()
    query = session.query(models.FeedUpdate).filter(
        models.FeedUpdate.feed_pk == feed.pk
    ).order_by(models.FeedUpdate.last_action_time.desc())
    for feed_update in query:
        yield feed_update


def create_update():
    return genericqueries.create(models.FeedUpdate)
