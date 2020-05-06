from unittest import mock

import pytest
import requests

from transiter import models, parse
from transiter.data.dams import feeddam
from transiter.services.update import updatemanager, sync

FEED_ID = "1"
SYSTEM_ID = "2"
FEED_UPDATE_PK = 3
MODULE_NAME = "module"
METHOD_NAME = "method"
CUSTOM_PARSER = "{}:{}".format(MODULE_NAME, METHOD_NAME)
URL = "http://www.feed.com"
FEED_CONTENT = "BlahBah"
OLD_FEED_CONTENT = "BlahBah2"


@pytest.mark.parametrize(
    "manager_function,expected_type",
    [
        [updatemanager.create_feed_update, models.FeedUpdate.Type.REGULAR],
        [updatemanager.create_feed_flush, models.FeedUpdate.Type.FLUSH],
    ],
)
@pytest.mark.parametrize(
    "feed_exists,expected_result", [[False, None], [True, FEED_UPDATE_PK]],
)
def test_create_feed_update(
    monkeypatch,
    inline_unit_of_work,
    manager_function,
    feed_exists,
    expected_result,
    expected_type,
):
    if feed_exists:
        feed = models.Feed(id=FEED_ID)
    else:
        feed = None
    monkeypatch.setattr(feeddam, "get_in_system_by_id", lambda *args, **kwargs: feed)

    def flush():
        nonlocal feed
        feed.updates[0].pk = FEED_UPDATE_PK

    inline_unit_of_work.flush.side_effect = flush

    actual_result = manager_function(SYSTEM_ID, FEED_ID)

    assert actual_result == expected_result

    if actual_result is None:
        return

    feed_update = feed.updates[0]
    assert feed_update.status == models.FeedUpdate.Status.SCHEDULED
    assert feed_update.update_type == expected_type


@pytest.mark.parametrize(
    "custom_parser,feed_content,previous_content,expected_status,expected_explanation",
    [
        [
            "invalid_package_definition",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.INVALID_PARSER,
        ],
        [
            "invalid_package:invalid_function",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.INVALID_PARSER,
        ],
        [
            "collections:invalid_function",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.INVALID_PARSER,
        ],
        [
            "collections:OrderedDict",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.DOWNLOAD_ERROR,
        ],
        [
            "collections:OrderedDict",
            b"",
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.EMPTY_FEED,
        ],
        [
            "collections:OrderedDict",
            b"content",
            b"content",
            models.FeedUpdate.Status.SUCCESS,
            models.FeedUpdate.Result.NOT_NEEDED,
        ],
        [
            "json:dumps",
            b"content",
            b"old_content",
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.PARSE_ERROR,
        ],
        [
            "builtins:list",
            b"content",
            b"old_content",
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.PARSE_ERROR,
        ],
        [
            1,
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Result.UNEXPECTED_ERROR,
        ],
    ],
)
def test_execute_feed_update(
    monkeypatch,
    inline_unit_of_work,
    custom_parser,
    feed_content,
    previous_content,
    expected_status,
    expected_explanation,
):
    system = models.System(id=SYSTEM_ID)
    feed = models.Feed(
        id=FEED_ID, system=system, custom_parser=custom_parser, url=URL, headers="{}"
    )
    feed_update = models.FeedUpdate(feed=feed)

    response = mock.MagicMock()
    if feed_content is None:
        response.raise_for_status.side_effect = requests.exceptions.RequestException()
    else:
        response.content = feed_content

    def get(*args, **kwargs):
        return response

    monkeypatch.setattr(requests, "get", get)

    def get_update_by_pk(feed_update_pk):
        return feed_update

    def get_last_successful_update(*args, **kwargs):
        if previous_content is None:
            return None
        return updatemanager._calculate_content_hash(previous_content)

    monkeypatch.setattr(feeddam, "get_update_by_pk", get_update_by_pk)
    monkeypatch.setattr(
        feeddam, "get_last_successful_update_hash", get_last_successful_update
    )
    monkeypatch.setattr(sync, "sync", lambda: (0, 0, 0))

    actual_status, actual_explanation = updatemanager.execute_feed_update(1)

    assert actual_status == expected_status
    assert actual_explanation == expected_explanation


@pytest.mark.parametrize(
    "sync_error,expected_status,expected_explanation",
    [
        [True, models.FeedUpdate.Status.FAILURE, models.FeedUpdate.Result.SYNC_ERROR],
        [False, models.FeedUpdate.Status.SUCCESS, models.FeedUpdate.Result.UPDATED],
    ],
)
def test_execute_feed_update__success_or_sync_error(
    inline_unit_of_work, monkeypatch, sync_error, expected_status, expected_explanation
):

    system = models.System(id=SYSTEM_ID)
    feed = models.Feed(
        id=FEED_ID, system=system, custom_parser="custom_parser", url=URL, headers="{}"
    )
    feed_update = models.FeedUpdate(feed=feed)

    response = mock.MagicMock()
    response.content = b"a"
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: response)

    monkeypatch.setattr(feeddam, "get_update_by_pk", lambda *args: feed_update)
    monkeypatch.setattr(feeddam, "get_last_successful_update_hash", lambda *args: None)

    class Parser(parse.TransiterParser):
        def load_content(self, content: bytes):
            pass

    monkeypatch.setattr(updatemanager, "_get_parser", lambda *args: Parser())

    def sync_func(feed_update_pk, entities):
        if sync_error:
            raise ValueError
        return 1, 2, 3

    monkeypatch.setattr(sync, "sync", sync_func)

    actual_status, actual_explanation = updatemanager.execute_feed_update(1)

    assert actual_status == expected_status
    assert actual_explanation == expected_explanation


def test_get_parser__built_in_parser__gtfs_static():
    parser = updatemanager._get_parser(models.Feed.BuiltInParser.GTFS_STATIC, None)

    assert isinstance(parser, parse.gtfsstatic.GtfsStaticParser)


def test_get_parser__built_in_parser__gtfs_realtime():
    assert parse.parser.cast_object_to_instantiated_transiter_parser(
        updatemanager._built_in_parser_to_function[
            models.Feed.BuiltInParser.GTFS_REALTIME
        ]
    ) == updatemanager._get_parser(models.Feed.BuiltInParser.GTFS_REALTIME, None)
