"""
The update manager contains the algorithm for executing feed updates.

This algorithm performs the following steps in order:

(1) Gets the parser for the Feed - either the built in parser or
    the custom parser. If this fails the update fails with explanation
    INVALID_PARSER.

(2) Downloads the data from the URL specified in the Feed. If this
    fails the update fails with explanation DOWNLOAD_ERROR. If the content
    of the download is empty, the update fails with explanation EMPTY_FEED.

(3) Calculate the hash of the downloaded data and compare it to the data
    used for the last successful FeedUpdate for this Feed. If they match,
    the update succeeds with explanation NOT_NEEDED.

(4) Perform the actual parsing using the Feed's parser. This "converts" the raw
    feed content into an iterator of UpdatableEntities. If any exception is
    raised by the parser then the update is failed with explanation
    PARSE_ERROR.

(5) Sync the results of the parser to the database using the sync module. If any
    exception is raised here, the update fails with explanation SYNC_ERROR.

(6) Otherwise, the update is deemed to be successful with explanation UPDATED.
"""
import hashlib
import importlib
import json
import logging
import time
import traceback
from typing import Tuple, Optional

import requests
from requests import RequestException

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import feeddam
from transiter.executor import celeryapp
from transiter.services.update import sync
from . import gtfsrealtimeparser, gtfsstaticparser

logger = logging.getLogger(__name__)


def create_feed_update(system_id, feed_id) -> Optional[int]:
    return _create_feed_update_helper(
        system_id, feed_id, update_type=models.FeedUpdate.Type.REGULAR
    )


def create_feed_flush(system_id, feed_id) -> Optional[int]:
    return _create_feed_update_helper(
        system_id, feed_id, update_type=models.FeedUpdate.Type.FLUSH
    )


@dbconnection.unit_of_work
def _create_feed_update_helper(system_id, feed_id, update_type) -> Optional[int]:
    feed = feeddam.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        return None
    feed_update = models.FeedUpdate()
    feed_update.update_type = update_type
    feed_update.status = feed_update.Status.SCHEDULED
    feed_update.feed = feed
    dbconnection.get_session().flush()
    return feed_update.pk


@celeryapp.app.task
def execute_feed_update_async(feed_update_pk, content=None):
    return execute_feed_update(feed_update_pk, content)


def execute_feed_update(
    feed_update_pk, content=None
) -> Tuple[models.FeedUpdate.Status, models.FeedUpdate.Explanation]:
    """
    Execute a feed update with logging and timing.

    For a description of what feed updates involve consult the module docs.

    :param feed_update_pk: the feed update's pk
    :param content: binary data to use for the update instead of downloading
                    data
    """

    start_time = time.time()
    try:
        status, explanation = _execute_feed_update_helper(feed_update_pk, content)
    except Exception as e:
        status, explanation = _update_status(
            feed_update_pk,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.UNEXPECTED_ERROR,
            str(traceback.format_exc()),
        )
        logger.exception("Unexpected error", e)
    execution_duration = time.time() - start_time
    with dbconnection.inline_unit_of_work():
        feed_update = feeddam.get_update_by_pk(feed_update_pk)
        feed_update.execution_duration = execution_duration
        log_prefix = "[{}/{}]".format(feed_update.feed.system.id, feed_update.feed.id)
    logger.info(
        "Feed update: {:7} / {:13} {:.2f} seconds  {}.".format(
            status.name, explanation.name, execution_duration, log_prefix,
        )
    )
    return status, explanation


class _InvalidParser(ValueError):
    """Exception raised when the Feed's parser is invalid."""

    pass


def _execute_feed_update_helper(
    feed_update_pk, content=None
) -> Tuple[models.FeedUpdate.Status, models.FeedUpdate.Explanation]:
    """
    Execute a feed update.

    For a description of what feed updates involve consult the module docs.

    :param feed_update_pk: the feed update
    :param content: binary data to use for the update instead of downloading
                    data
    """
    with dbconnection.inline_unit_of_work():
        feed_update = feeddam.get_update_by_pk(feed_update_pk)
        update_type = feed_update.update_type
        feed = feed_update.feed
        feed_update.status = feed_update.Status.IN_PROGRESS

        feed_pk = feed.pk
        built_in_parser = feed.built_in_parser
        custom_parser = feed.custom_parser
        feed_url = feed.url
        feed_headers = feed.headers

    if update_type == models.FeedUpdate.Type.FLUSH:
        return _sync_entities(feed_update_pk, [])

    try:
        parser = _get_parser(built_in_parser, custom_parser)
    except _InvalidParser:
        return _update_status(
            feed_update_pk,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.INVALID_PARSER,
            str(traceback.format_exc()),
        )

    if content is None:
        try:
            content = _get_content(feed_url, feed_headers)
        except RequestException as download_error:
            return _update_status(
                feed_update_pk,
                models.FeedUpdate.Status.FAILURE,
                models.FeedUpdate.Explanation.DOWNLOAD_ERROR,
                str(download_error),
            )

    feed_update.content_length = len(content)
    if len(content) == 0:
        return _update_status(
            feed_update_pk,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.EMPTY_FEED,
        )

    content_hash = _calculate_content_hash(content)
    with dbconnection.inline_unit_of_work():
        feed_update = feeddam.get_update_by_pk(feed_update_pk)
        feed_update.raw_data_hash = content_hash
        previous_hash = feeddam.get_last_successful_update_hash(feed_pk)
    if previous_hash is not None and previous_hash == content_hash:
        return _update_status(
            feed_update_pk,
            feed_update.Status.SUCCESS,
            feed_update.Explanation.NOT_NEEDED,
        )

    # We catch any exception that can be thrown in the feed parser as, from our
    # perspective, the feed parser is foreign code.
    # noinspection PyBroadException
    try:
        entities = parser(binary_content=content)
    except Exception:
        return _update_status(
            feed_update_pk,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.PARSE_ERROR,
            str(traceback.format_exc()),
        )
    return _sync_entities(feed_update_pk, entities)


def _sync_entities(feed_update_pk, entities):
    # noinspection PyBroadException
    try:
        with dbconnection.inline_unit_of_work():
            sync.sync(feed_update_pk, entities)
            feed_update = feeddam.get_update_by_pk(feed_update_pk)
            feed_update.status = models.FeedUpdate.Status.SUCCESS
            feed_update.explanation = models.FeedUpdate.Explanation.UPDATED
            return feed_update.status, feed_update.explanation
    except Exception as e:
        logger.exception("Unexpected sync error", e)
        return _update_status(
            feed_update_pk,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.SYNC_ERROR,
            str(traceback.format_exc()),
        )


_built_in_parser_to_function = {
    models.Feed.BuiltInParser.GTFS_STATIC: gtfsstaticparser.parse_gtfs_static,
    models.Feed.BuiltInParser.GTFS_REALTIME: gtfsrealtimeparser.built_in_parser,
}


@dbconnection.unit_of_work
def _update_status(
    feed_update_pk, status, explanation, failure_message=None, execution_duration=None
):
    # TODO: use an update query for this b/c it will happen a lot
    feed_update = feeddam.get_update_by_pk(feed_update_pk)
    feed_update.status = status
    feed_update.explanation = explanation
    if failure_message is not None:
        feed_update.failure_message = failure_message
    if execution_duration is not None:
        feed_update.execution_duration = execution_duration
    return status, explanation


def _get_parser(built_in_parser, custom_parser):
    """
    Get the parser for a feed.

    :param feed: the feed
    :return: the parser
    :rtype: func
    """
    if built_in_parser is not None:
        return _built_in_parser_to_function[built_in_parser]

    colon_char = custom_parser.find(":")
    if colon_char == -1:
        raise _InvalidParser(
            "Custom parser specifier must be of the form module:method"
        )
    module_str = custom_parser[:colon_char]
    method_str = custom_parser[(colon_char + 1) :]

    # The broad exception here is to capture any buggy code in the module being
    # imported.
    # noinspection PyBroadException
    try:
        module = _import_module(module_str)
    except ModuleNotFoundError:
        raise _InvalidParser("Unknown module '{}'".format(module_str))
    except Exception:
        raise _InvalidParser(f"Failed to import module {module_str}")

    try:
        return getattr(module, method_str)
    except AttributeError:
        raise _InvalidParser(
            "Module '{}' has no method '{}'.".format(module_str, method_str)
        )


def _import_module(module_str, invalidate_caches=True):
    """
    Import a module.

    With invalidate caches True, if the import fails caches will be invalidated
    and the import attempted once more. Otherwise only one attempt is made.

    :param module_str: the module's name
    :param invalidate_caches: described above
    :return: the module
    """
    try:
        return importlib.import_module(module_str)
    except ModuleNotFoundError:
        if invalidate_caches:
            importlib.invalidate_caches()
            return _import_module(module_str, invalidate_caches=False)
        else:
            raise


def _get_content(feed_url, feed_headers):
    """
    Download data from the Feed's URL.

    :param feed: the Feed
    :return: binary data
    """
    request = requests.get(feed_url, timeout=4, headers=json.loads(feed_headers))
    request.raise_for_status()
    return request.content


def _calculate_content_hash(content):
    """
    Calculate the MD5 hash of binary data.

    :param content: binary data
    :return: MD5 hash
    """
    m = hashlib.md5()
    m.update(content)
    return m.hexdigest()
