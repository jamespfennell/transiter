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
import datetime
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
) -> Tuple[models.FeedUpdate.Status, models.FeedUpdate.Result]:
    """
    Execute a feed update with logging and timing.

    For a description of what feed updates involve consult the module docs.
    """

    start_time = time.time()
    try:
        feed_update = _execute_feed_update_helper(feed_update_pk, content)
    except Exception as e:
        feed_update = models.FeedUpdate(
            pk=feed_update_pk,
            status=models.FeedUpdate.Status.FAILURE,
            result=models.FeedUpdate.Result.UNEXPECTED_ERROR,
            result_message=str(traceback.format_exc()),
        )
        logger.exception("Unexpected error", e)
    feed_update.total_duration = time.time() - start_time
    feed_update.completed_at = datetime.datetime.utcnow()
    with dbconnection.inline_unit_of_work() as session:
        session.merge(feed_update)
    logger.info(
        "{:7} / {:13} {:.2f} seconds / feed pk = {}.".format(
            feed_update.status.name,
            feed_update.result.name,
            feed_update.total_duration,
            feed_update.feed_pk,
        )
    )
    return feed_update.status, feed_update.result


class _InvalidParser(ValueError):
    """Exception raised when the Feed's parser is invalid."""

    pass


def _execute_feed_update_helper(feed_update_pk: int, content=None) -> models.FeedUpdate:
    """
    Execute a feed update.

    For a description of what feed updates involve consult the module docs.
    """
    with dbconnection.inline_unit_of_work() as session:
        feed_update = feeddam.get_update_by_pk(feed_update_pk)
        feed = feed_update.feed
        feed_update.status = feed_update.Status.IN_PROGRESS
        # We need to flush the session to persist the status change.
        session.flush()
        session.expunge(feed_update)
        session.expunge(feed)

    if feed_update.update_type == models.FeedUpdate.Type.FLUSH:
        return _sync_entities(feed_update, [])

    try:
        parser = _get_parser(feed.built_in_parser, feed.custom_parser)
    except _InvalidParser:
        return _update_status(
            feed_update,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.INVALID_PARSER,
            str(traceback.format_exc()),
        )

    if content is None:
        try:
            download_start_time = time.time()
            content = _get_content(feed.url, feed.headers)
        except RequestException as download_error:
            return _update_status(
                feed_update,
                models.FeedUpdate.Status.FAILURE,
                models.FeedUpdate.Result.DOWNLOAD_ERROR,
                str(download_error),
            )
        feed_update.download_duration = time.time() - download_start_time

    feed_update.content_length = len(content)
    if feed_update.content_length == 0:
        return _update_status(
            feed_update,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.EMPTY_FEED,
        )

    feed_update.content_hash = _calculate_content_hash(content)
    with dbconnection.inline_unit_of_work():
        previous_hash = feeddam.get_last_successful_update_hash(feed.pk)
    if previous_hash is not None and previous_hash == feed_update.content_hash:
        return _update_status(
            feed_update,
            models.FeedUpdate.Status.SUCCESS,
            models.FeedUpdate.Result.NOT_NEEDED,
        )

    # We catch any exception that can be thrown in the feed parser as, from our
    # perspective, the feed parser is foreign code.
    # noinspection PyBroadException
    try:
        entities = parser(binary_content=content)
    except Exception:
        return _update_status(
            feed_update,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.PARSE_ERROR,
            str(traceback.format_exc()),
        )

    return _sync_entities(feed_update, entities)


def _sync_entities(feed_update: models.FeedUpdate, entities):
    entities_iter = IteratorWithConsumedCount(entities)
    try:
        with dbconnection.inline_unit_of_work() as session:
            (
                feed_update.num_added_entities,
                feed_update.num_updated_entities,
                feed_update.num_deleted_entities,
            ) = sync.sync(feed_update.pk, entities_iter)
            feed_update.num_parsed_entities = entities_iter.num_consumed()
            feed_update.status = models.FeedUpdate.Status.SUCCESS
            feed_update.result = models.FeedUpdate.Result.UPDATED
            session.merge(feed_update)
            return feed_update
    except Exception as e:
        logger.exception("Unexpected sync error", e)
        return _update_status(
            feed_update,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.SYNC_ERROR,
            str(traceback.format_exc()),
        )


_built_in_parser_to_function = {
    models.Feed.BuiltInParser.GTFS_STATIC: gtfsstaticparser.parse_gtfs_static,
    models.Feed.BuiltInParser.GTFS_REALTIME: gtfsrealtimeparser.built_in_parser,
}


def _update_status(feed_update: models.FeedUpdate, status, result, result_message=None):
    feed_update.status = status
    feed_update.result = result
    if result_message is not None:
        feed_update.result_message = result_message
    return feed_update


def _get_parser(built_in_parser, custom_parser):
    """
    Get the parser for a feed.
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
    Download data from the feed's URL.
    """
    request = requests.get(feed_url, timeout=4, headers=json.loads(feed_headers))
    request.raise_for_status()
    return request.content


def _calculate_content_hash(content):
    """
    Calculate the MD5 hash of binary data.
    """
    m = hashlib.md5()
    m.update(content)
    return m.hexdigest()


class IteratorWithConsumedCount:
    """
    Class that wraps around iterators and tracks the number of items consumed; i.e.,
    the number of elements that have been iterated over.
    """

    def __init__(self, iterable):
        self._num_consumed = None
        self._iterator = iter(iterable)

    def __iter__(self):
        self._num_consumed = 0
        return self

    def __next__(self):
        element = self._iterator.__next__()
        self._num_consumed += 1
        return element

    def num_consumed(self):
        return self._num_consumed
