import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import stopqueries, systemqueries, transfersconfigqueries
from transiter.services import transfersconfigservice, views

SYSTEM_1_ID = "1"
SYSTEM_2_ID = "2"
STOP_1_ID = "3"
STOP_2_ID = "4"
STOP_3_ID = "5"
SYSTEM_1 = models.System(id=SYSTEM_1_ID)
SYSTEM_2 = models.System(id=SYSTEM_2_ID)


def list_all_in_system_factory(stops):
    return lambda system_id: [stop for stop in stops if stop.system.id == system_id]


@pytest.mark.parametrize(
    "stops,distance,expected_tuples",
    [
        [  # Base case
            [
                models.Stop(id=STOP_1_ID, latitude=1, longitude=1, system=SYSTEM_1),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_2),
            ],
            50000,
            {(STOP_1_ID, STOP_3_ID), (STOP_3_ID, STOP_1_ID)},
        ],
        [  # No matches
            [
                models.Stop(id=STOP_1_ID, latitude=1, longitude=1, system=SYSTEM_1),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_2),
            ],
            500,
            set(),
        ],
        [  # All stops in one system
            [
                models.Stop(id=STOP_1_ID, latitude=1, longitude=1, system=SYSTEM_1),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_1),
            ],
            50000,
            set(),
        ],
        [
            # Child matches case
            [
                models.Stop(
                    id=STOP_1_ID,
                    latitude=1,
                    longitude=1,
                    system=SYSTEM_1,
                    parent_stop=models.Stop(id=STOP_2_ID),
                ),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_2),
            ],
            50000,
            {(STOP_2_ID, STOP_3_ID), (STOP_3_ID, STOP_2_ID)},
        ],
    ],
)
def test_build_transfers(monkeypatch, stops, distance, expected_tuples):
    monkeypatch.setattr(
        stopqueries, "list_all_in_system", list_all_in_system_factory(stops),
    )

    actual_pairs = {
        (transfer.from_stop.id, transfer.to_stop.id)
        for transfer in transfersconfigservice._build_transfers(
            [SYSTEM_1, SYSTEM_2], distance
        )
    }

    assert expected_tuples == actual_pairs


@pytest.mark.parametrize(
    "function",
    [
        transfersconfigservice.create,
        transfersconfigservice.preview,
        lambda *args: transfersconfigservice.update(None, *args),
    ],
)
@pytest.mark.parametrize("inputted_system_ids", [{"1"}, {"1", "1"}, set(), {"1", "3"}])
def test_list_systems_invalid_input(monkeypatch, function, inputted_system_ids):

    actual_system_ids = {"1", "2"}

    monkeypatch.setattr(
        systemqueries,
        "list_all",
        lambda system_ids: [
            models.System(id=id_) for id_ in actual_system_ids if id_ in system_ids
        ],
    )
    monkeypatch.setattr(
        transfersconfigqueries, "get", lambda args: models.TransfersConfig
    )
    with pytest.raises(exceptions.InvalidInput):
        function(inputted_system_ids, 100)


@pytest.mark.parametrize(
    "function",
    [
        transfersconfigservice.get_by_id,
        transfersconfigservice.delete,
        lambda config_id: transfersconfigservice.update(config_id, None, None),
    ],
)
def test_get_config_does_not_exist(monkeypatch, function):
    monkeypatch.setattr(transfersconfigqueries, "get", lambda args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        function(100)


CONFIG_PK = 1
CONFIG_ID = "1"
DISTANCE = 2
SYSTEM_ID = "3"


def test_list_all(monkeypatch, system_1_model, system_1_view):
    monkeypatch.setattr(
        transfersconfigqueries,
        "list_all",
        lambda: [
            models.TransfersConfig(
                pk=CONFIG_PK, distance=DISTANCE, systems=[system_1_model], transfers=[],
            )
        ],
    )

    expected = [
        views.TransfersConfig(id=CONFIG_ID, distance=DISTANCE, systems=[system_1_view])
    ]

    assert expected == transfersconfigservice.list_all()


def test_get_by_id(
    monkeypatch,
    system_1_model,
    system_1_view,
    stop_1_model,
    stop_1_small_view,
    stop_2_model,
    stop_2_small_view,
):
    monkeypatch.setattr(
        transfersconfigqueries,
        "get",
        lambda config_id: models.TransfersConfig(
            pk=CONFIG_PK,
            distance=DISTANCE,
            systems=[system_1_model],
            transfers=[
                models.Transfer(
                    from_stop=stop_1_model,
                    to_stop=stop_2_model,
                    type=models.Transfer.Type.GEOGRAPHIC,
                )
            ],
        ),
    )

    stop_1_small_view.system = system_1_view
    stop_2_small_view.system = system_1_view

    expected = views.TransfersConfigBig(
        id=CONFIG_ID,
        distance=DISTANCE,
        systems=[system_1_view],
        transfers=[
            views.Transfer(
                from_stop=stop_1_small_view,
                to_stop=stop_2_small_view,
                type=models.Transfer.Type.GEOGRAPHIC,
            )
        ],
    )

    assert expected == transfersconfigservice.get_by_id(CONFIG_PK)
