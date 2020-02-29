import pytest

from transiter import models


@pytest.fixture
def system_1(add_model):
    return add_model(
        models.System(pk=1, id="2", status=models.System.SystemStatus.ACTIVE)
    )


@pytest.fixture
def system_2(add_model):
    return add_model(
        models.System(pk=3, id="4", status=models.System.SystemStatus.ACTIVE)
    )


@pytest.fixture
def installing_system(add_model):
    return add_model(
        models.System(pk=5, id="6", status=models.System.SystemStatus.INSTALLING)
    )
