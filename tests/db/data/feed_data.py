import datetime

import pytest

from transiter.db import models


@pytest.fixture
def feed_1_1(add_model, system_1):
    return add_model(
        models.Feed(pk=301, id="302", system=system_1, auto_update_enabled=True)
    )


@pytest.fixture
def feed_1_2(add_model, system_1):
    return add_model(
        models.Feed(pk=303, id="304", system=system_1, auto_update_enabled=False)
    )


@pytest.fixture
def feed_2_1(add_model, system_2):
    return add_model(
        models.Feed(pk=311, id="312", system=system_2, auto_update_enabled=True)
    )


@pytest.fixture
def feed_1_1_update_1(add_model, feed_1_1):
    return add_model(
        models.FeedUpdate(
            pk=351,
            feed=feed_1_1,
            status=models.FeedUpdate.Status.SUCCESS,
            completed_at=datetime.datetime(2011, 1, 1, 1, 0, 0),
        )
    )


@pytest.fixture
def feed_1_1_update_2(add_model, feed_1_1):
    return add_model(
        models.FeedUpdate(
            pk=353,
            feed=feed_1_1,
            status=models.FeedUpdate.Status.SUCCESS,
            completed_at=datetime.datetime(2011, 1, 1, 3, 0, 0),
            content_hash="BLAH",
        )
    )


@pytest.fixture
def feed_1_1_update_3(add_model, feed_1_1):
    return add_model(
        models.FeedUpdate(
            pk=355,
            feed=feed_1_1,
            status=models.FeedUpdate.Status.FAILURE,
            completed_at=datetime.datetime(2011, 1, 1, 5, 0, 0),
        )
    )
