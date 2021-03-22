from typing import Optional

from sqlalchemy import sql, func
from sqlalchemy.orm import joinedload

from transiter.db import dbconnection, models
from transiter.db.queries import genericqueries


def list_all_feed_pks():
    return list(pk_ for (pk_,) in dbconnection.get_session().query(models.Feed.pk))


def list_all_active():
    """
    List all feeds in active systems.
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.Feed)
        .join(models.System, models.System.pk == models.Feed.system_pk)
        .filter(models.System.status == models.System.SystemStatus.ACTIVE)
    )
    return query.all()


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
    return genericqueries.list_in_system(models.Feed, system_id, models.Feed.id)


def get_in_system_by_id(system_id, feed_id):
    """
    Get a Feed in a System.

    :param system_id: the system's ID
    :param feed_id: the feed's ID
    :return: Feed, if it exists; None, otherwise
    """
    return genericqueries.get_in_system_by_id(models.Feed, system_id, feed_id)


def get_update_by_pk(feed_update_pk) -> Optional[models.FeedUpdate]:
    session = dbconnection.get_session()
    return (
        session.query(models.FeedUpdate)
        .filter(models.FeedUpdate.pk == feed_update_pk)
        .options(joinedload(models.FeedUpdate.feed))
        .options(joinedload(models.FeedUpdate.feed, models.Feed.system))
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
            sql.select(1).where(UpdatableEntity.source_pk == models.FeedUpdate.pk)
        )
        for UpdatableEntity in models.list_updatable_entities()
    ]
    query = (
        sql.delete(models.FeedUpdate)
        .where(
            sql.and_(
                models.FeedUpdate.feed_pk == feed_pk,
                models.FeedUpdate.completed_at <= before_datetime,
                *not_exists_conditions
            )
        )
        .execution_options(synchronize_session=False)
    )
    dbconnection.get_session().execute(query)


def delete_in_system_by_id(system_id, feed_id):
    """
    Delete a Feed from the DB whose ID is given.

    :return: True if an entity was found and deleted, false if no such
     entity exists
    """
    session = dbconnection.get_session()
    entity = get_in_system_by_id(system_id, feed_id)
    if entity is None:
        return False
    session.delete(entity)
    return True


def list_aggregated_updates(feed_pks, start_time):
    session = dbconnection.get_session()
    query = (
        session.query(
            models.FeedUpdate.feed_pk,
            func.count(models.FeedUpdate.status),
            models.FeedUpdate.status,
            models.FeedUpdate.result,
            func.min(models.FeedUpdate.completed_at),
            func.max(models.FeedUpdate.completed_at),
        )
        .group_by(
            models.FeedUpdate.feed_pk,
            models.FeedUpdate.status,
            models.FeedUpdate.result,
        )
        .filter(
            models.FeedUpdate.feed_pk.in_(feed_pks),
            models.FeedUpdate.completed_at > start_time,
            models.FeedUpdate.status.in_(
                {models.FeedUpdate.Status.SUCCESS, models.FeedUpdate.Status.FAILURE}
            ),
        )
    )
    feed_pk_to_updates = {}
    for row in query.all():
        if row[0] not in feed_pk_to_updates:
            feed_pk_to_updates[row[0]] = []
        feed_pk_to_updates[row[0]].append(row[1:])
    return feed_pk_to_updates
