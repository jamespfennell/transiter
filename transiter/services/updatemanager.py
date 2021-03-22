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

(5) Sync the results of the parser to the database using the import module. If any
    exception is raised here, the update fails with explanation SYNC_ERROR.

(6) Otherwise, the update is deemed to be successful with explanation UPDATED.
"""
import datetime
import dataclasses
import hashlib
import importlib
import json
import logging
import time
import traceback
import typing

import requests
from requests import RequestException

from transiter import import_
from transiter.db import dbconnection, models
from transiter.db.queries import feedqueries
from transiter.executor import celeryapp
from transiter.parse import parser, gtfsstatic, gtfsrealtime, TransiterParser
from transiter.scheduler import client

logger = logging.getLogger(__name__)


def create_feed_update(system_id, feed_id) -> typing.Optional[int]:
    return _create_feed_update_helper(
        system_id, feed_id, update_type=models.FeedUpdate.Type.REGULAR
    )


def create_feed_flush(system_id, feed_id) -> typing.Optional[int]:
    return _create_feed_update_helper(
        system_id, feed_id, update_type=models.FeedUpdate.Type.FLUSH
    )


@dbconnection.unit_of_work
def _create_feed_update_helper(system_id, feed_id, update_type) -> typing.Optional[int]:
    feed = feedqueries.get_in_system_by_id(system_id, feed_id)
    if feed is None:
        return None
    feed_update = models.FeedUpdate()
    feed_update.update_type = update_type
    feed_update.status = feed_update.Status.SCHEDULED
    feed_update.feed = feed
    dbconnection.get_session().add(feed_update)
    dbconnection.get_session().flush()
    return feed_update.pk


@celeryapp.app.task
def execute_feed_update_async(feed_update_pk, content=None):
    return execute_feed_update(feed_update_pk, content)


def execute_feed_update(
    feed_update_pk, content=None
) -> typing.Tuple[models.FeedUpdate, typing.Optional[Exception]]:
    """
    Execute a feed update with logging and timing.

    For a description of what feed updates involve consult the module docs.
    """

    context = _initialize_update_context(feed_update_pk, content)

    if context.feed_update.update_type == models.FeedUpdate.Type.FLUSH:
        actions = _FLUSH_UPDATE_ACTIONS
    else:
        actions = _REGULAR_UPDATE_ACTIONS

    stats = None
    exception = None
    for action in actions:
        try:
            stats = action(context)
        except Exception as e:
            logger.exception("Exception encountered during update")
            exception_type_to_outcome = getattr(
                action, "__exception_type_to_outcome__", {}
            )
            for exception_type, (status, result) in exception_type_to_outcome.items():
                if isinstance(e, exception_type):
                    context.feed_update.status = status
                    context.feed_update.result = result
                    context.feed_update.result_message = str(traceback.format_exc())
                    exception = e
                    break
            if context.feed_update.result_message is None:
                context.feed_update.status = models.FeedUpdate.Status.FAILURE
                context.feed_update.result = models.FeedUpdate.Result.UNEXPECTED_ERROR
                context.feed_update.result_message = str(traceback.format_exc())
                exception = e

        # If the action or one of its error handlers marked a status on the update, we
        # need to finish right now.
        if context.feed_update.status != models.FeedUpdate.Status.IN_PROGRESS:
            break

    context.feed_update.total_duration = time.time() - context.start_time
    context.feed_update.completed_at = datetime.datetime.utcnow()
    with dbconnection.inline_unit_of_work() as session:
        session.merge(context.feed_update)
    logger.info(
        "{:7} / {:13} {:.2f} seconds / feed pk = {}.".format(
            context.feed_update.status.name,
            context.feed_update.result.name,
            context.feed_update.total_duration,
            context.feed_update.feed_pk,
        )
    )
    client.feed_update_callback(
        context.feed_update.feed_pk,
        context.feed_update.status,
        context.feed_update.result,
        stats.entity_type_to_num_in_db() if stats is not None else {},
    )
    return context.feed_update, exception


class _InvalidParser(ValueError):
    """Exception raised when the Feed's parser is invalid."""

    pass


@dataclasses.dataclass
class _UpdateContext:
    feed_update: models.FeedUpdate
    content: typing.Optional[bytes] = None
    parser: typing.Optional[TransiterParser] = None
    start_time: int = dataclasses.field(default_factory=time.time)


def _initialize_update_context(feed_update_pk, content) -> _UpdateContext:
    with dbconnection.inline_unit_of_work() as session:
        feed_update = feedqueries.get_update_by_pk(feed_update_pk)
        feed = feed_update.feed
        feed_update.status = feed_update.Status.IN_PROGRESS
        # We need to flush the session to persist the status change.
        session.flush()
        session.expunge(feed_update)
        session.expunge(feed)
    return _UpdateContext(feed_update=feed_update, content=content)


def _possible_exception(exception_type, status, result):
    """
    Decorator for special exception handling in update step functions.
    """

    def decorator(f):
        if not hasattr(f, "__exception_type_to_outcome__"):
            f.__exception_type_to_outcome__ = {}
        f.__exception_type_to_outcome__[exception_type] = (status, result)
        return f

    return decorator


@_possible_exception(
    _InvalidParser,
    models.FeedUpdate.Status.FAILURE,
    models.FeedUpdate.Result.INVALID_PARSER,
)
def _get_parser_t(context: _UpdateContext):
    context.parser = _get_parser(
        context.feed_update.feed.built_in_parser, context.feed_update.feed.custom_parser
    )


def _get_parser_for_flush(context: _UpdateContext):
    context.parser = parser.CallableBasedParser(lambda: [])


@_possible_exception(
    RequestException,
    models.FeedUpdate.Status.FAILURE,
    models.FeedUpdate.Result.DOWNLOAD_ERROR,
)
def _get_content(context: _UpdateContext):
    if context.content is not None:
        return
    download_start_time = time.time()
    request = requests.get(
        context.feed_update.feed.url,
        timeout=context.feed_update.feed.http_timeout or 10,
        headers=json.loads(context.feed_update.feed.headers),
    )
    request.raise_for_status()
    context.content = request.content
    context.feed_update.download_duration = time.time() - download_start_time


def _check_for_non_empty_content(context: _UpdateContext):
    context.feed_update.content_length = (
        len(context.content) if context.content is not None else 0
    )
    if context.feed_update.content_length == 0:
        context.feed_update.status = models.FeedUpdate.Status.FAILURE
        context.feed_update.result = models.FeedUpdate.Result.EMPTY_FEED


def _calculate_content_hash(context: _UpdateContext):
    m = hashlib.md5()
    m.update(context.content)
    context.feed_update.content_hash = m.hexdigest()
    with dbconnection.inline_unit_of_work():
        previous_hash = feedqueries.get_last_successful_update_hash(
            context.feed_update.feed.pk
        )
    if previous_hash is not None and previous_hash == context.feed_update.content_hash:
        context.feed_update.status = models.FeedUpdate.Status.SUCCESS
        context.feed_update.result = models.FeedUpdate.Result.NOT_NEEDED


# We catch any exception that can be thrown in the feed parser as, from our
# perspective, the feed parser is foreign code.
# noinspection PyBroadException
@_possible_exception(
    Exception, models.FeedUpdate.Status.FAILURE, models.FeedUpdate.Result.PARSE_ERROR,
)
def _load_options_into_parser(context: _UpdateContext):
    raw_options = context.feed_update.feed.parser_options
    if raw_options is None:
        return
    options = json.loads(raw_options)
    context.parser.load_options(options)


# We catch any exception that can be thrown in the feed parser as, from our
# perspective, the feed parser is foreign code.
# noinspection PyBroadException
@_possible_exception(
    Exception, models.FeedUpdate.Status.FAILURE, models.FeedUpdate.Result.PARSE_ERROR,
)
def _load_content_into_parser(context: _UpdateContext):
    context.parser.load_content(context.content)


@_possible_exception(
    Exception, models.FeedUpdate.Status.FAILURE, models.FeedUpdate.Result.IMPORT_ERROR,
)
def _import(context: _UpdateContext):
    feed_update = context.feed_update
    with dbconnection.inline_unit_of_work() as session:
        stats = import_.run_import(feed_update.pk, context.parser)

        feed_update.num_added_entities = stats.num_added()
        feed_update.num_updated_entities = stats.num_updated()
        feed_update.num_deleted_entities = stats.num_deleted()
        feed_update.num_parsed_entities = -1
        feed_update.status = models.FeedUpdate.Status.SUCCESS
        feed_update.result = models.FeedUpdate.Result.UPDATED

        session.merge(feed_update)
        return stats


_REGULAR_UPDATE_ACTIONS = [
    _get_parser_t,
    _load_options_into_parser,
    _get_content,
    _check_for_non_empty_content,
    _calculate_content_hash,
    _load_content_into_parser,
    _import,
]

_FLUSH_UPDATE_ACTIONS = [_get_parser_for_flush, _import]


_built_in_parser_to_function = {
    models.Feed.BuiltInParser.GTFS_STATIC: gtfsstatic.GtfsStaticParser,
    models.Feed.BuiltInParser.GTFS_REALTIME: gtfsrealtime.GtfsRealtimeParser,
}


def _get_parser(built_in_parser, custom_parser) -> parser.TransiterParser:
    """
    Get the parser for a feed.
    """
    if built_in_parser is not None:
        return parser.cast_object_to_instantiated_transiter_parser(
            _built_in_parser_to_function[built_in_parser]
        )

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
        module_attr = getattr(module, method_str)
    except AttributeError:
        raise _InvalidParser(
            "Module '{}' has no method '{}'.".format(module_str, method_str)
        )

    try:
        return parser.cast_object_to_instantiated_transiter_parser(module_attr)
    except ValueError:
        raise _InvalidParser(
            "Attribute '{}' of module '{}' is not a valid Transiter parser.".format(
                method_str, module_str
            )
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
