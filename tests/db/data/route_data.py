import pytest

from transiter.db import models

ROUTE_1_1_ID = "202"


@pytest.fixture
def route_1_1(add_model, system_1, feed_1_1_update_1):
    return add_model(
        models.Route(pk=201, id=ROUTE_1_1_ID, system=system_1, source=feed_1_1_update_1)
    )


@pytest.fixture
def route_1_2(add_model, system_1, feed_1_1_update_1):
    return add_model(
        models.Route(pk=203, id="204", system=system_1, source=feed_1_1_update_1)
    )


@pytest.fixture
def route_1_3(add_model, system_1, feed_1_1_update_1):
    return add_model(
        models.Route(pk=205, id="206", system=system_1, source=feed_1_1_update_1)
    )


@pytest.fixture
def route_2_1(add_model, system_2, feed_2_1_update_1):
    return add_model(
        models.Route(pk=207, id="208", system=system_2, source=feed_2_1_update_1)
    )
