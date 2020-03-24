"""
The feed service is used to retrieve data about feeds and perform feed update
operations.
"""

import datetime
import logging

from transiter import exceptions
from transiter.data import dbconnection
from transiter.data.dams import feeddam, systemdam
from transiter.services import links, constants as c
from transiter.services.update import updatemanager

logger = logging.getLogger(__name__)


@dbconnection.unit_of_work
def list_all_auto_updating():
    """
    List all auto updating feeds. This method is designed for use by the task
    server.

    :return: a list of dictionaries containing keys pk, id, system_id and
             auto_update_period.
    :rtype: list
    """
    response = []
    for feed in feeddam.list_all_auto_updating():
        response.append(
            {
                "pk": feed.pk,
                "id": feed.id,
                "system_id": feed.system.id,
                "auto_update_period": feed.auto_update_period,
            }
        )
    return response


@dbconnection.unit_of_work
def list_all_in_system(system_id, return_links=True):
    """
    Get data on all feeds in a system.

    The result is list of dictionaries, one for each feed, containing the
    feed's short representation and (optionally) a link to the feed.

    :param system_id: the system ID
    :type system_id: str
    :param return_links: whether to return links
    :type return_links: bool
    :type system_id: str
    :return: the list described above
    :rtype: list
    """
    system = systemdam.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError
    response = []
    for feed in feeddam.list_all_in_system(system_id):
        feed_response = feed.to_dict()
        if return_links:
            feed_response[c.HREF] = links.FeedEntityLink(feed)
        response.append(feed_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, feed_id, return_links=True):
    """
    Get data on a specific feed in a system.

    :param system_id: the system ID
    :type system_id: str
    :param feed_id: the feed ID
    :type feed_id: str
    :param return_links: whether to return a link to the feed's updates page.
    :type return_links: bool
    :return: the feed's short representation.
    :rtype: dict
    """
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError
    response = feed.to_dict()
    if return_links:
        response[c.UPDATES] = {c.HREF: links.FeedEntityUpdatesLink(feed)}
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
        raise exceptions.IdNotFoundError
    if execute_async:
        updatemanager.execute_feed_update_async.delay(feed_update_pk, content)
    else:
        updatemanager.execute_feed_update(feed_update_pk, content)
    return feed_update_pk


@dbconnection.unit_of_work
def list_updates_in_feed(system_id, feed_id):
    """
    List all of the updates for a feed.

    :param system_id: the system ID
    :type system_id: str
    :param feed_id: the feed ID
    :type feed_id: str
    :return: a list of short representations of the feed updates.
    :rtype: list
    """
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError
    response = []
    for feed_update in feeddam.list_updates_in_feed(feed.pk):
        response.append(feed_update.to_dict())
    return response


@dbconnection.unit_of_work
def get_update_in_feed_by_pk(system_id, feed_id, feed_update_pk):
    feed_update = feeddam.get_update_by_pk(feed_update_pk)
    if feed_update is None:
        raise exceptions.IdNotFoundError
    return feed_update.to_dict()


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
