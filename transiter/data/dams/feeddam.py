from typing import Optional

from sqlalchemy import sql

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries


def list_all_feed_pks():
    return list(pk_ for (pk_,) in dbconnection.get_session().query(models.Feed.pk))


def list_all_auto_updating():
    """
    List all auto-updating Feeds.

    :return: list of Feeds
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.Feed)
        .join(models.System, models.System.pk == models.Feed.system_pk)
        .filter(models.Feed.auto_update_enabled)
        .filter(models.System.auto_update_enabled)
        .filter(models.System.status == models.System.SystemStatus.ACTIVE)
    )
    return query.all()


def list_all_in_system(system_id):
    """
    List all Feeds in a System.

    :param system_id: the system's ID
    :return: list of Feeds
    """
    return genericqueries.list_all_in_system(models.Feed, system_id, models.Feed.id)


def get_in_system_by_id(system_id, feed_id):
    """
    Get a Feed in a System.

    :param system_id: the system's ID
    :param feed_id: the feed's ID
    :return: Feed, if it exists; None, otherwise
    """
    return genericqueries.get_in_system_by_id(models.Feed, system_id, feed_id)


def get_update_by_pk(feed_update_pk) -> Optional[models.FeedUpdate]:
    # TODO: greedily add the feed and the system if not already
    session = dbconnection.get_session()
    return (
        session.query(models.FeedUpdate)
        .filter(models.FeedUpdate.pk == feed_update_pk)
        .one_or_none()
    )


def get_last_successful_update_hash(feed_pk) -> Optional[str]:
    """
    Get the last successful FeedUpdate content hash for a Feed.

    :param feed_pk: the feed's PK
    :return: FeedUpdate, or None if it doesn't exist
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.FeedUpdate.content_hash)
        .filter(models.FeedUpdate.feed_pk == feed_pk)
        .order_by(models.FeedUpdate.completed_at.desc())
        .filter(models.FeedUpdate.status == "SUCCESS")
        .limit(1)
    )
    result = query.first()
    if result is None:
        return None
    return result[0]


def list_updates_in_feed(feed_pk):
    """
    List the most recent updates in a feed, ordered descending in time.

    :param feed_pk: the Feed's PK
    :return: list of FeedUpdates
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.FeedUpdate)
        .filter(models.FeedUpdate.feed_pk == feed_pk)
        .order_by(models.FeedUpdate.pk.desc())
        .limit(100)
    )
    return query.all()


def trim_feed_updates(feed_pk, before_datetime):
    """
    Trip all FeedUpdates for a feed whose last action time was before
    a certain cut-off point.

    :param feed_pk: pk of the feed
    :param before_datetime: the cut-off point
    """
    not_exists_conditions = [
        ~sql.exists(
            sql.select([sql.literal_column("1")]).where(
                UpdatableEntity.source_pk == models.FeedUpdate.pk
            )
        )
        for UpdatableEntity in models.list_updatable_entities()
    ]
    query = sql.delete(models.FeedUpdate).where(
        sql.and_(
            models.FeedUpdate.feed_pk == feed_pk,
            models.FeedUpdate.completed_at <= before_datetime,
            *not_exists_conditions
        )
    )
    dbconnection.get_session().execute(query)
