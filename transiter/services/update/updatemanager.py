import hashlib
import importlib
import logging
import time
import traceback

import requests

from transiter import models
from transiter.data.dams import feeddam
from . import gtfsrealtimeutil, gtfsstaticutil

logger = logging.getLogger(__name__)


class InvalidParser(ValueError):
    pass


class DownloadError(Exception):
    pass


def execute_feed_update(feed_update, content=None):
    start_time = time.time()
    _execute_feed_update_helper(feed_update, content)
    feed_update.execution_duration = time.time() - start_time
    log_prefix = '[{}/{}]'.format(
        feed_update.feed.system.id,
        feed_update.feed.id
    )
    logger.debug(
        '{} Feed update for took {} seconds'.format(
            log_prefix,
            feed_update.execution_duration
        )
    )


def _execute_feed_update_helper(feed_update: models.FeedUpdate, content=None):
    feed = feed_update.feed
    feed_update.status = feed_update.Status.IN_PROGRESS

    try:
        parser = _get_parser(feed)
    except InvalidParser as invalid_parser:
        feed_update.status = feed_update.Status.FAILURE
        feed_update.explanation = feed_update.Explanation.INVALID_PARSER
        feed_update.failure_message = str(invalid_parser)
        return

    if content is None:
        try:
            content = _get_content(feed)
        except requests.RequestException as download_error:
            feed_update.status = feed_update.Status.FAILURE
            feed_update.explanation = feed_update.Explanation.DOWNLOAD_ERROR
            feed_update.failure_message = str(download_error)
            return

    content_hash = _calculate_content_hash(content)
    feed_update.raw_data_hash = content_hash
    last_successful_update = feeddam.get_last_successful_update(feed.pk)
    if (
            last_successful_update is not None and
            last_successful_update.raw_data_hash == feed_update.raw_data_hash
    ):
        feed_update.status = feed_update.Status.SUCCESS
        feed_update.explanation = feed_update.Explanation.NOT_NEEDED
        return

    try:
        parser(feed, content)
    except Exception:
        feed_update.status = feed_update.Status.FAILURE
        feed_update.explanation = feed_update.Explanation.PARSE_ERROR
        feed_update.failure_message = str(traceback.format_exc())
        logger.debug('Feed parse error:\n' + feed_update.failure_message)
        return

    feed_update.status = feed_update.Status.SUCCESS
    feed_update.explanation = feed_update.Explanation.UPDATED

# TODO: test that this is populated for all built in parsers
_built_in_parser_to_function = {
    models.Feed.BuiltInParser.GTFS_STATIC: gtfsstaticutil.parse_gtfs_static,
    models.Feed.BuiltInParser.GTFS_REALTIME: gtfsrealtimeutil.gtfs_realtime_parser
}


def _get_parser(feed: models.Feed):
    if feed.built_in_parser is not None:
        return _built_in_parser_to_function[feed.built_in_parser]

    parser_str = feed.custom_parser

    colon_char = parser_str.find(':')
    if colon_char == -1:
        raise InvalidParser(
            'Custom parser specifier must be of the form module:method'
        )
    module_str = parser_str[:colon_char]
    method_str = parser_str[colon_char + 1:]

    try:
        module = _import_module(module_str)
    except ModuleNotFoundError:
        raise InvalidParser('Unknown module \'{}\''.format(module_str))

    try:
        return getattr(module, method_str)
    except AttributeError:
        raise InvalidParser('Module \'{}\' has no method \'{}\'.'.format(
            module_str, method_str))


def _import_module(module_str, invalidate_caches=False):
    try:
        return importlib.import_module(module_str)
    except ModuleNotFoundError:
        if invalidate_caches:
            return _import_module(module_str, invalidate_caches=True)
        else:
            raise


def _get_content(feed):
    request = requests.get(feed.url)
    request.raise_for_status()
    return request.content


def _calculate_content_hash(content):
    m = hashlib.md5()
    m.update(content)
    return m.hexdigest()
