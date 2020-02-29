import pytest

from transiter import models


@pytest.fixture
def route_1_1(add_model, system_1):
    return add_model(models.Route(pk=201, id="202", system=system_1))


@pytest.fixture
def route_1_2(add_model, system_1):
    return add_model(models.Route(pk=203, id="204", system=system_1))


@pytest.fixture
def route_1_3(add_model, system_1):
    return add_model(models.Route(pk=205, id="206", system=system_1))


@pytest.fixture
def route_2_1(add_model, system_2):
    return add_model(models.Route(pk=207, id="208", system=system_2))
