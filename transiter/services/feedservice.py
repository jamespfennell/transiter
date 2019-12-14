"""
The feed service is used to retrieve data about feeds and perform feed update
operations.
"""

import datetime
import logging

from transiter import models, exceptions
from transiter.data import dbconnection
from transiter.data.dams import feeddam, systemdam
from transiter.services import links
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
    for feed in feeddam.list_all_autoupdating():
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
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError
    response = []
    for feed in feeddam.list_all_in_system(system_id):
        feed_response = feed.short_repr()
        if return_links:
            feed_response["href"] = links.FeedEntityLink(feed)
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
    response = feed.short_repr()
    if return_links:
        response["updates"] = {"href": links.FeedEntityUpdatesLink(feed)}
    return response


@dbconnection.unit_of_work
def create_feed_update(system_id, feed_id, content=None):
    """
    Create a feed update for a feed in a system.

    :param system_id: the system ID
    :type system_id: str
    :param feed_id: the feed ID
    :type feed_id: str
    :param content: the content to use for the feed update.
    :return: the feed update's long representation.
    :rtype: dict
    """
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        raise exceptions.IdNotFoundError
    feed_update = models.FeedUpdate(feed)
    updatemanager.execute_feed_update(feed_update, content)
    return {**feed_update.long_repr()}


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
        response.append(feed_update.short_repr())
    return response


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
