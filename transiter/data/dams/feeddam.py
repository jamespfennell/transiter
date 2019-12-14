from sqlalchemy import func, sql

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries


def list_all_feed_pks():
    return list(pk_ for (pk_,) in dbconnection.get_session().query(models.Feed.pk))


def list_all_autoupdating():
    """
    List all auto-updating Feeds.

    :return: list of Feeds
    """
    session = dbconnection.get_session()
    query = session.query(models.Feed).filter(models.Feed.auto_update_on)
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


def get_last_successful_update(feed_pk):
    """
    Get the last successful FeedUpdate for a Feed.

    :param feed_pk: the feed's PK
    :return: FeedUpdate, or None if it doesn't exist
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.FeedUpdate)
        .filter(models.FeedUpdate.feed_pk == feed_pk)
        .order_by(models.FeedUpdate.last_action_time.desc())
        .filter(models.FeedUpdate.status == "SUCCESS")
        .limit(1)
    )
    return query.first()


def list_updates_in_feed(feed_pk):
    """
    List the updates in a feed, order descending in time.

    :param feed_pk: the Feed's PK
    :return: list of FeedUpdates
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.FeedUpdate)
        .filter(models.FeedUpdate.feed_pk == feed_pk)
        .order_by(models.FeedUpdate.last_action_time.desc())
    )
    return query.all()


def trim_feed_updates(feed_pk, before_datetime):
    """
    Trip all FeedUpdates for a feed whose last action time was before
    a certain cut-off point.

    :feed_pk: pk of the feed
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
            models.FeedUpdate.last_action_time <= before_datetime,
            *not_exists_conditions
        )
    )
    dbconnection.get_session().execute(query)


def aggregate_feed_updates(before_datetime):
    """
    Return aggregate data about FeedUpdates in the system before a certain
    cut-off time.

    This function groups FeedUpdates into bins based on their (1) Feed
    (2) status and (3) explanation. The result of this function is a list of
    tuples, one tuple for each bin. Each tuple has 6 elements:

    (1) the system ID of FeedUpdates in this bin
    (2) the feed ID
    (3) the status
    (4) the explanation
    (5) the number of FeedUpdates in this bin
    (6) the average execution duration for FeedUpdates in this bin

    :param before_datetime: the cut-off time
    :return: the list described above
    """
    session = dbconnection.get_session()
    query = (
        sql.select(
            [
                models.Feed.system_id,
                models.Feed.id.label("feed_id"),
                models.FeedUpdate.status,
                models.FeedUpdate.explanation,
                func.count().label("count"),
                func.avg(models.FeedUpdate.execution_duration).label(
                    "avg_execution_duration"
                ),
            ]
        )
        .select_from(sql.join(models.Feed, models.FeedUpdate))
        .group_by(
            models.Feed.system_id,
            models.Feed.id,
            models.FeedUpdate.status,
            models.FeedUpdate.explanation,
        )
        .where(models.FeedUpdate.last_action_time <= before_datetime)
        .order_by(models.Feed.system_id, models.Feed.id, models.FeedUpdate.status)
    )
    return [row for row in session.execute(query)]
