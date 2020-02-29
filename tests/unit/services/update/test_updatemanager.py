from unittest import mock

import pytest
import requests

from transiter import models
from transiter.data.dams import feeddam
from transiter.services.update import updatemanager

FEED_ID = "1"
SYSTEM_ID = "2"
MODULE_NAME = "module"
METHOD_NAME = "method"
CUSTOM_PARSER = "{}:{}".format(MODULE_NAME, METHOD_NAME)
URL = "http://www.feed.com"
FEED_CONTENT = "BlahBah"
OLD_FEED_CONTENT = "BlahBah2"


@pytest.mark.parametrize(
    "custom_parser,feed_content,previous_content,expected_status,expected_explanation",
    [
        [
            "invalid_package:invalid_function",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.INVALID_PARSER,
        ],
        [
            "collections:invalid_function",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.INVALID_PARSER,
        ],
        [
            "collections:OrderedDict",
            None,
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.DOWNLOAD_ERROR,
        ],
        [
            "collections:OrderedDict",
            b"",
            None,
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.EMPTY_FEED,
        ],
        [
            "collections:OrderedDict",
            b"content",
            b"content",
            models.FeedUpdate.Status.SUCCESS,
            models.FeedUpdate.Explanation.NOT_NEEDED,
        ],
        [
            "json:dumps",
            b"content",
            b"old_content",
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.PARSE_ERROR,
        ],
        [
            "collections:OrderedDict",
            b"content",
            b"old_content",
            models.FeedUpdate.Status.FAILURE,
            models.FeedUpdate.Explanation.SYNC_ERROR,
        ],
    ],
)
def test_execute_feed_update(
    monkeypatch,
    no_op_unit_of_work,
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

    def _update_status(feed_update_pk, status, explanation, *args, **kwargs):
        return status, explanation

    monkeypatch.setattr(updatemanager, "_update_status", _update_status)

    actual_status, actual_explanation = updatemanager.execute_feed_update(1)

    assert actual_status == expected_status
    assert actual_explanation == expected_explanation
