import pytest

from transiter.db import models


@pytest.fixture
def system_1(add_model):
    return add_model(
        models.System(
            pk=1, id="2", status=models.System.SystemStatus.ACTIVE, name="System 1"
        )
    )


@pytest.fixture
def system_2(add_model):
    return add_model(
        models.System(
            pk=3, id="4", status=models.System.SystemStatus.ACTIVE, name="System 2"
        )
    )


@pytest.fixture
def agency_1_1(add_model, system_1):
    return add_model(
        models.Agency(
            id="6", name="Agency", timezone="America/New York", system=system_1
        )
    )


@pytest.fixture
def installing_system(add_model):
    return add_model(
        models.System(
            pk=5, id="6", status=models.System.SystemStatus.INSTALLING, name="System 3"
        )
    )
