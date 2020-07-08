import pytest

from transiter.db import models


@pytest.fixture
def stop_1_1(add_model, system_1, feed_1_1_update_1):
    return add_model(
        models.Stop(
            pk=101,
            id="102",
            system=system_1,
            type=models.Stop.Type.STATION,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def stop_1_2(add_model, system_1, feed_1_1_update_1):
    return add_model(
        models.Stop(
            pk=103,
            id="104",
            system=system_1,
            type=models.Stop.Type.STATION,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def stop_1_3(add_model, system_1, stop_1_2, feed_1_1_update_1):
    return add_model(
        models.Stop(
            pk=105,
            id="106",
            system=system_1,
            type=models.Stop.Type.PLATFORM,
            parent_stop_pk=stop_1_2.pk,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def stop_1_4(add_model, system_1, stop_1_2, feed_1_1_update_1):
    return add_model(
        models.Stop(
            pk=107,
            id="108",
            system=system_1,
            type=models.Stop.Type.STATION,
            parent_stop_pk=stop_1_2.pk,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def stop_1_5(add_model, system_1, feed_1_1_update_1):
    return add_model(
        models.Stop(
            pk=109,
            id="110",
            system=system_1,
            type=models.Stop.Type.STATION,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def stop_2_1(add_model, system_2, feed_2_1_update_1):
    return add_model(
        models.Stop(
            pk=111,
            id="112",
            system=system_2,
            type=models.Stop.Type.PLATFORM,
            source=feed_2_1_update_1,
        )
    )
