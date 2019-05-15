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
def list_all_in_system(system_id, return_links=False):
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
def get_in_system_by_id(system_id, feed_id, return_links=False):
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


@dbconnection.unit_of_work
def trim_feed_updates():
    """
    Delete old feed updates.

    This method deletes feed updates that were created more than 60 minutes
    ago. Before deleting the updates, it prints some aggregate statistics
    such as the proportion of feed updates that were successful.

    This method is designed to be called hourly by the task server. It is only
    meant to be a short term solution to the problem of cleaning and documenting
    old feed updates: in the future, aggregate feed update reports should be
    persisted in the database.
    """
    logger.info("Trimming old feed updates.")
    before_datetime = (
        datetime.datetime.now() - datetime.timedelta(minutes=60)
    ).replace(microsecond=0, second=0)
    logger.info("\n" + _build_feed_updates_report(before_datetime))
    logger.info("Deleting feed updates in DB before {}".format(before_datetime))
    feeddam.trim_feed_updates(before_datetime)


def _build_feed_updates_report(before_datetime):
    table_row_template = "{delimiter}".join(
        [
            "{system_id:13}",
            "{feed_id:20}",
            "{status:10}",
            "{explanation:20}",
            "{count:>5}",
            "{avg_execution_duration:>6}",
        ]
    )
    table_rows = [
        "Aggregated feed update report for updates in the database before {}".format(
            before_datetime
        ),
        "",
        "Column explanations:",
        "+ number of feed updates of this type",
        "* average execution time for feed updates of this type",
        "",
        table_row_template.format(
            delimiter=" | ",
            system_id="system_id",
            feed_id="feed_id",
            status="status",
            explanation="explanation",
            count="*",
            avg_execution_duration="+",
        ),
    ]
    feed_id = None
    status = None
    for feed_update_data in feeddam.aggregate_feed_updates(before_datetime):
        if feed_update_data["feed_id"] != feed_id:
            table_rows.append(
                table_row_template.format(
                    delimiter="-+-",
                    system_id="-" * 13,
                    feed_id="-" * 20,
                    status="-" * 10,
                    explanation="-" * 20,
                    count="-" * 5,
                    avg_execution_duration="-" * 6,
                )
            )
            feed_id = table_feed_id = feed_update_data["feed_id"]
            table_system_id = feed_update_data["system_id"]
        else:
            table_feed_id = ""
            table_system_id = ""

        if feed_update_data["status"] != status or table_feed_id != "":
            status = table_status = feed_update_data["status"].name
        else:
            table_status = ""

        table_rows.append(
            table_row_template.format(
                delimiter=" | ",
                system_id=table_system_id,
                feed_id=table_feed_id,
                status=table_status,
                explanation=feed_update_data["explanation"].name,
                count=feed_update_data["count"],
                avg_execution_duration="{:.2f}".format(
                    feed_update_data["avg_execution_duration"]
                ),
            )
        )

    return "\n".join(table_rows)
