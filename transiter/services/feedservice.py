"""
The feed service is used to retrieve data about feeds and perform feed update
operations.
"""

import datetime
import logging
import typing

from transiter import exceptions, models
from transiter.data import dbconnection
from transiter.data.dams import feeddam, systemdam
from transiter.services import views
from transiter.services.update import updatemanager

logger = logging.getLogger(__name__)


@dbconnection.unit_of_work
def list_all_auto_updating() -> typing.List[views.Feed]:
    """
    List all auto updating feeds.
    """
    return [
        views.Feed.from_model(feed, add_system=True)
        for feed in feeddam.list_all_auto_updating()
    ]


@dbconnection.unit_of_work
def list_all_in_system(system_id) -> typing.List[views.Feed]:
    """
    Get data on all feeds in a system.
    """
    system = systemdam.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    return list(map(views.Feed.from_model, feeddam.list_all_in_system(system_id)))


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, feed_id) -> views.Feed:
    """
    Get data on a specific feed in a system.
    """
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError(
            models.Feed, system_id=system_id, feed_id=feed_id
        )
    response = views.FeedLarge.from_model(feed)
    response.updates = views.UpdatesInFeedLink.from_model(feed)
    return response


def create_and_execute_feed_update(
    system_id, feed_id, content=None, execute_async=False
):
    return _create_and_execute_feed_update_helper(
        system_id,
        feed_id,
        update_manager_function=updatemanager.create_feed_update,
        content=content,
        execute_async=execute_async,
    )


def create_and_execute_feed_flush(system_id, feed_id, execute_async=False):
    return _create_and_execute_feed_update_helper(
        system_id,
        feed_id,
        update_manager_function=updatemanager.create_feed_flush,
        content=None,
        execute_async=execute_async,
    )


def _create_and_execute_feed_update_helper(
    system_id, feed_id, update_manager_function, content=None, execute_async=False,
):
    """
    Create a feed update for a feed in a system.
    """
    feed_update_pk = update_manager_function(system_id, feed_id)
    if feed_update_pk is None:
        raise exceptions.IdNotFoundError(
            models.Feed, system_id=system_id, feed_id=feed_id
        )
    if execute_async:
        updatemanager.execute_feed_update_async.delay(feed_update_pk, content)
    else:
        updatemanager.execute_feed_update(feed_update_pk, content)
    return feed_update_pk


@dbconnection.unit_of_work
def list_updates_in_feed(system_id, feed_id):
    """
    List all of the updates for a feed.
    """
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError(
            models.Feed, system_id=system_id, feed_id=feed_id
        )
    response = []
    for feed_update in feeddam.list_updates_in_feed(feed.pk):
        response.append(views.FeedUpdate.from_model(feed_update))
    return response


@dbconnection.unit_of_work
def get_update_in_feed_by_pk(system_id, feed_id, feed_update_pk):
    feed_update = feeddam.get_update_by_pk(feed_update_pk)
    if feed_update is None:
        raise exceptions.IdNotFoundError(
            models.Feed,
            system_id=system_id,
            feed_id=feed_id,
            feed_update_id=str(feed_update_pk),
        )
    return views.FeedUpdate.from_model(feed_update)


def trim_feed_updates():
    """
    Delete old feed updates.

    This method is designed to be called hourly by the task server.
    """

    @dbconnection.unit_of_work
    def _list_all_feed_pks():
        return feeddam.list_all_feed_pks()

    @dbconnection.unit_of_work
    def _trim_feed_updates_helper(feed_pk_, before_datetime_):
        logger.info(
            "Deleting feed updates with feed_pk={} and last updated before {}".format(
                feed_pk_, before_datetime_
            )
        )
        feeddam.trim_feed_updates(feed_pk_, before_datetime_)

    logger.info("Trimming old feed updates.")
    before_datetime = (
        datetime.datetime.now() - datetime.timedelta(minutes=60)
    ).replace(microsecond=0, second=0)

    for feed_pk in _list_all_feed_pks():
        _trim_feed_updates_helper(feed_pk, before_datetime)
