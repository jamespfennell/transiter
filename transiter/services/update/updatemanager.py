"""
The update manager contains the algorithm for executing feed updates.

This algorithm performs the following steps in order:

(1) Attempt to get the parser for the Feed - either the built in parser or
    the custom parser. If this fails the update fails with explanation
    INVALID_PARSER.

(2) Attempt to download the data from the URL specified in the Feed. If this
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

import requests
from requests import RequestException

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import feeddam
from transiter.services.update import sync
from . import gtfsrealtimeparser, gtfsstaticparser

logger = logging.getLogger(__name__)


def execute_feed_update(feed_update, content=None):
    """
    Execute a feed update with logging and timing.

    For a description of what feed updates involve consult the module docs.

    :param feed_update: the feed update
    :param content: binary data to use for the update instead of downloading
                    data
    """
    start_time = time.time()
    _execute_feed_update_helper(feed_update, content)
    dbconnection.get_session().flush()
    feed_update.execution_duration = time.time() - start_time
    log_prefix = "[{}/{}]".format(feed_update.feed.system.id, feed_update.feed.id)
    logger.info(
        "Feed update: {:7} / {:13} {:.2f} seconds  {}.".format(
            feed_update.status.name,
            feed_update.explanation.name,
            feed_update.execution_duration,
            log_prefix,
        )
    )


class _InvalidParser(ValueError):
    """Exception raised when the Feed's parser is invalid."""

    pass


def _execute_feed_update_helper(feed_update: models.FeedUpdate, content=None):
    """
    Execute a feed update.

    For a description of what feed updates involve consult the module docs.

    :param feed_update: the feed update
    :param content: binary data to use for the update instead of downloading
                    data
    """
    feed = feed_update.feed
    feed_update.status = feed_update.Status.IN_PROGRESS
    try:
        parser = _get_parser(feed)
    except _InvalidParser:
        feed_update.status = feed_update.Status.FAILURE
        feed_update.explanation = feed_update.Explanation.INVALID_PARSER
        feed_update.failure_message = str(traceback.format_exc())
        logger.info("Feed parser import error:\n" + feed_update.failure_message)
        return

    if content is None:
        try:
            content = _get_content(feed)
        except RequestException as download_error:
            feed_update.status = feed_update.Status.FAILURE
            feed_update.explanation = feed_update.Explanation.DOWNLOAD_ERROR
            feed_update.failure_message = str(download_error)
            return

    feed_update.content_length = len(content)
    if len(content) == 0:
        feed_update.status = feed_update.Status.FAILURE
        feed_update.explanation = feed_update.Explanation.EMPTY_FEED
        return

    content_hash = _calculate_content_hash(content)
    feed_update.raw_data_hash = content_hash
    last_successful_update = feeddam.get_last_successful_update(feed.pk)
    if (
        last_successful_update is not None
        and last_successful_update.raw_data_hash == feed_update.raw_data_hash
    ):
        feed_update.status = feed_update.Status.SUCCESS
        feed_update.explanation = feed_update.Explanation.NOT_NEEDED
        return

    # We catch any exception that can be thrown in the feed parser as, from our
    # perspective, the feed parser is foreign code.
    # noinspection PyBroadException
    try:
        entities = parser(binary_content=content)
    except Exception:
        feed_update.status = feed_update.Status.FAILURE
        feed_update.explanation = feed_update.Explanation.PARSE_ERROR
        feed_update.failure_message = str(traceback.format_exc())
        logger.info("Feed parse error:\n" + feed_update.failure_message)
        return

    # noinspection PyBroadException
    try:
        sync.sync(feed_update, entities)
    except Exception:
        feed_update.status = feed_update.Status.FAILURE
        feed_update.explanation = feed_update.Explanation.SYNC_ERROR
        feed_update.failure_message = str(traceback.format_exc())
        logger.info(
            "Error syncing parsed results to the DB:\n" + feed_update.failure_message
        )
        return

    feed_update.status = feed_update.Status.SUCCESS
    feed_update.explanation = feed_update.Explanation.UPDATED


_built_in_parser_to_function = {
    models.Feed.BuiltInParser.GTFS_STATIC: gtfsstaticparser.parse_gtfs_static,
    models.Feed.BuiltInParser.GTFS_REALTIME: gtfsrealtimeparser.built_in_parser,
}


def _get_parser(feed: models.Feed):
    """
    Get the parser for a feed.

    :param feed: the feed
    :return: the parser
    :rtype: func
    """
    if feed.built_in_parser is not None:
        return _built_in_parser_to_function[feed.built_in_parser]

    parser_str = feed.custom_parser

    colon_char = parser_str.find(":")
    if colon_char == -1:
        raise _InvalidParser(
            "Custom parser specifier must be of the form module:method"
        )
    module_str = parser_str[:colon_char]
    method_str = parser_str[(colon_char + 1) :]

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


def _get_content(feed: models.Feed):
    """
    Download data from the Feed's URL.

    :param feed: the Feed
    :return: binary data
    """
    request = requests.get(feed.url, timeout=4, headers=json.loads(feed.headers))
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
