import json
import time
import unittest.mock as mock
import uuid

import pytest

from transiter import exceptions
from transiter.db import dbconnection, models
from transiter.db.queries import feedqueries, genericqueries, systemqueries
from transiter.scheduler import client
from transiter.services import systemservice, systemconfigreader, views, updatemanager

SYSTEM_ONE_ID = "1"
SYSTEM_ONE_NAME = "1-name"
SYSTEM_TWO_ID = "2"
SYSTEM_TWO_HREF = "4"
SYSTEM_TWO_REPR = {"system_id": SYSTEM_TWO_ID, "href": SYSTEM_TWO_HREF}
SYSTEM_ONE_NUM_STOPS = 20
SYSTEM_ONE_NUM_STATIONS = 21
SYSTEM_ONE_NUM_ROUTES = 22
SYSTEM_ONE_NUM_FEEDS = 23
SYSTEM_ONE_NUM_AGENCIES = 24
FILE_NAME = "24"
STOP_ONE_ID = "25"
PARSED_SYSTEM_CONFIG = {
    "name": "Name",
    "requirements": {"packages": [], "extra_settings": {}},
    "feeds": "Blah blah blah",
    "service_maps": "ser",
    "direction_rules_files": [],
}


def test_list_all(monkeypatch):
    monkeypatch.setattr(
        systemqueries,
        "list_all",
        lambda: [
            models.System(
                id=SYSTEM_ONE_ID,
                name=SYSTEM_ONE_NAME,
                status=models.System.SystemStatus.ACTIVE,
            )
        ],
    )

    expected = [
        views.System(
            id=SYSTEM_ONE_ID,
            name=SYSTEM_ONE_NAME,
            status=models.System.SystemStatus.ACTIVE,
        )
    ]

    actual = systemservice.list_all()

    assert expected == actual


def test_get_by_id_no__such_system(monkeypatch):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        systemservice.get_by_id(SYSTEM_ONE_ID)


def test_get_by_id(monkeypatch):
    def count(relationship, system):
        return {
            models.System.stops: SYSTEM_ONE_NUM_STOPS,
            models.System.feeds: SYSTEM_ONE_NUM_FEEDS,
            models.System.routes: SYSTEM_ONE_NUM_ROUTES,
            models.System.agencies: SYSTEM_ONE_NUM_AGENCIES,
        }[relationship]

    system = models.System(
        id=SYSTEM_ONE_ID, name=SYSTEM_ONE_NAME, status=models.System.SystemStatus.ACTIVE
    )

    expected = views.SystemLarge(
        id=SYSTEM_ONE_ID,
        status=models.System.SystemStatus.ACTIVE,
        name=SYSTEM_ONE_NAME,
        agencies=views.AgenciesInSystem(
            count=SYSTEM_ONE_NUM_AGENCIES, _system_id=SYSTEM_ONE_ID
        ),
        stops=views.StopsInSystem(count=SYSTEM_ONE_NUM_STOPS, _system_id=SYSTEM_ONE_ID),
        routes=views.RoutesInSystem(
            count=SYSTEM_ONE_NUM_ROUTES, _system_id=SYSTEM_ONE_ID
        ),
        feeds=views.FeedsInSystem(count=SYSTEM_ONE_NUM_FEEDS, _system_id=SYSTEM_ONE_ID),
    )

    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args: system)
    monkeypatch.setattr(genericqueries, "count_number_of_related_entities", count)

    actual = systemservice.get_by_id(SYSTEM_ONE_ID)

    assert expected == actual


feeds_config = {
    "feed": {
        "parser": {"built_in": models.Feed.BuiltInParser.GTFS_REALTIME},
        "http": {"url": "URL", "headers": {}},
        "auto_update": {"enabled": True, "period": 5},
        "required_for_install": False,
    }
}


@pytest.fixture
def mock_systemdam(monkeypatch):
    class SystemDam:
        def __init__(self):
            self._system = None
            self._update = None

        def get_update_by_pk(self, system_update_pk):
            if (
                self._update is None
                and self._system is not None
                and self._system.updates is not None
                and len(self._system.updates) > 0
            ):
                self._update = self._system.updates[0]
            return self._update

        def create_update(self, update):
            update.system = self._system
            self._update = update

        def get_by_id(self, *args, **kwargs):
            return self._system

        def create(self, system=None):
            if system is None:
                self._system = models.System()
            else:
                self._system = system
            return self._system

        def delete_by_id(self, system_id):
            self._system = None

    mock_systemdam = SystemDam()
    monkeypatch.setattr(
        systemqueries, "get_update_by_pk", mock_systemdam.get_update_by_pk
    )
    monkeypatch.setattr(systemqueries, "get_by_id", mock_systemdam.get_by_id)
    monkeypatch.setattr(systemqueries, "create", mock_systemdam.create)
    monkeypatch.setattr(systemqueries, "delete_by_id", mock_systemdam.delete_by_id)
    return mock_systemdam


SYSTEM_ID = "401"
SYSTEM_UPDATE_PK = 403
CURRENT_TIMESTAMP = 243552
FEED_ID_1 = "201"
FEED_PK_1 = 202
FEED_ID_2 = "203"
FEED_PK_2 = 204
FEED_ID_3 = "205"


@pytest.mark.parametrize(
    "feed_update_status,delete_fail,final_system_status,delete_called",
    [
        [
            models.FeedUpdate.Status.FAILURE,
            False,
            models.System.SystemStatus.INSTALL_FAILED,
            False,
        ],
        [
            models.FeedUpdate.Status.SUCCESS,
            True,
            models.System.SystemStatus.INSTALL_FAILED,
            True,
        ],
        [
            models.FeedUpdate.Status.SUCCESS,
            False,
            models.System.SystemStatus.ACTIVE,
            True,
        ],
    ],
)
def test_install(
    mock_systemdam,
    inline_unit_of_work,
    monkeypatch,
    feed_update_status,
    delete_called,
    final_system_status,
    delete_fail,
):

    _delete_feed = mock.MagicMock()
    if delete_fail:
        _delete_feed.side_effect = ValueError
    monkeypatch.setattr(systemservice, "_delete_feed", _delete_feed)
    monkeypatch.setattr(
        systemservice,
        "_install_system_configuration",
        lambda *args, **kwargs: ([FEED_ID_1], [FEED_ID_2]),
    )
    monkeypatch.setattr(client, "refresh_tasks", lambda: None)
    monkeypatch.setattr(
        updatemanager,
        "execute_feed_update",
        lambda *args, **kwargs: (models.FeedUpdate(status=feed_update_status), None),
    )
    monkeypatch.setattr(updatemanager, "create_feed_update", mock.MagicMock())

    systemservice.install(SYSTEM_ID, "adsf", {"key": "value"}, None)

    system = mock_systemdam.get_by_id(SYSTEM_ID)
    assert system.status is final_system_status

    if delete_called:
        _delete_feed.assert_called_once()


@pytest.mark.parametrize("prior_auto_update_setting", [True, False])
@pytest.mark.parametrize(
    "initial_system_status,post_system_status",
    [
        [models.System.SystemStatus.SCHEDULED, models.System.SystemStatus.INSTALLING],
        [models.System.SystemStatus.ACTIVE, models.System.SystemStatus.ACTIVE],
    ],
)
def test_mark_update_started(
    mock_systemdam,
    monkeypatch,
    prior_auto_update_setting,
    initial_system_status,
    post_system_status,
):
    monkeypatch.setattr(time, "time", lambda: CURRENT_TIMESTAMP)

    system = models.System(
        auto_update_enabled=prior_auto_update_setting,
        status=initial_system_status,
        id=SYSTEM_ID,
    )
    mock_systemdam.create(system)
    mock_systemdam.create_update(
        models.SystemUpdate(
            pk=SYSTEM_UPDATE_PK, status=models.SystemUpdate.Status.SCHEDULED
        )
    )

    context = systemservice._mark_update_started(SYSTEM_UPDATE_PK)

    assert context == systemservice._SystemUpdateContext(
        update_pk=SYSTEM_UPDATE_PK,
        system_id=SYSTEM_ID,
        prior_auto_update_setting=prior_auto_update_setting,
        start_time=CURRENT_TIMESTAMP,
    )
    assert system.status == post_system_status
    assert system.auto_update_enabled is False


@pytest.mark.parametrize("prior_auto_update_setting", [True, False])
@pytest.mark.parametrize(
    "initial_system_status,final_status,post_system_status",
    [
        [
            models.System.SystemStatus.INSTALLING,
            models.SystemUpdate.Status.SUCCESS,
            models.System.SystemStatus.ACTIVE,
        ],
        [
            models.System.SystemStatus.ACTIVE,
            models.SystemUpdate.Status.SUCCESS,
            models.System.SystemStatus.ACTIVE,
        ],
        [
            models.System.SystemStatus.INSTALLING,
            models.SystemUpdate.Status.FAILED,
            models.System.SystemStatus.INSTALL_FAILED,
        ],
        [
            models.System.SystemStatus.ACTIVE,
            models.SystemUpdate.Status.FAILED,
            models.System.SystemStatus.ACTIVE,
        ],
    ],
)
def test_mark_update_completed(
    mock_systemdam,
    monkeypatch,
    prior_auto_update_setting,
    initial_system_status,
    final_status,
    post_system_status,
):
    monkeypatch.setattr(time, "time", lambda: CURRENT_TIMESTAMP + 99)

    system = models.System(
        auto_update_enabled=False, status=initial_system_status, id=SYSTEM_ID,
    )
    mock_systemdam.create(system)
    update = models.SystemUpdate(
        pk=SYSTEM_UPDATE_PK, status=models.SystemUpdate.Status.IN_PROGRESS
    )
    mock_systemdam.create_update(update)

    context = systemservice._SystemUpdateContext(
        update_pk=SYSTEM_UPDATE_PK,
        system_id=SYSTEM_ID,
        prior_auto_update_setting=prior_auto_update_setting,
        start_time=CURRENT_TIMESTAMP,
    )

    systemservice._mark_update_completed(context, final_status, "message")

    assert update.status is final_status
    assert update.status_message == "message"
    assert update.total_duration == 99
    assert system.auto_update_enabled is prior_auto_update_setting
    assert system.status is post_system_status


@pytest.mark.parametrize(
    "current_status",
    [
        models.System.SystemStatus.SCHEDULED,
        models.System.SystemStatus.INSTALLING,
        models.System.SystemStatus.DELETING,
    ],
)
def test_create_system_update__invalid_current_status(mock_systemdam, current_status):
    system = mock_systemdam.create()
    system.status = current_status
    with pytest.raises(exceptions.InstallError):
        systemservice._create_system_update("system_id", "", {}, None)


@pytest.mark.parametrize(
    "current_status,post_status",
    [
        [models.System.SystemStatus.ACTIVE, models.System.SystemStatus.ACTIVE],
        [
            models.System.SystemStatus.INSTALL_FAILED,
            models.System.SystemStatus.SCHEDULED,
        ],
    ],
)
def test_create_system_update__exists_already(
    mock_systemdam, current_status, post_status, inline_unit_of_work
):
    system = mock_systemdam.create()
    system.status = current_status

    systemservice._create_system_update("system_id", "", {}, None)

    assert system.status is post_status
    assert len(system.updates) == 1
    assert system.updates[0].status == models.SystemUpdate.Status.SCHEDULED


def test_create_system_update__does_not_exist(mock_systemdam, inline_unit_of_work):
    systemservice._create_system_update("system_id", "", {}, None)

    system = mock_systemdam.get_by_id("system_id")

    assert system is not None
    assert system.status is models.System.SystemStatus.SCHEDULED
    assert len(system.updates) == 1
    assert system.updates[0].status == models.SystemUpdate.Status.SCHEDULED


def _test_install(mock_systemdam, monkeypatch, inline_unit_of_work):

    monkeypatch.setattr(systemqueries, "get_by_id", mock_systemdam.get_by_id)
    monkeypatch.setattr(systemqueries, "create", mock_systemdam.create)

    _install_service_maps = mock.MagicMock()
    monkeypatch.setattr(
        systemservice, "_save_service_map_configuration", _install_service_maps
    )
    _install_feeds = mock.MagicMock()
    monkeypatch.setattr(systemservice, "_save_feed_configuration", _install_feeds)

    read = mock.MagicMock()
    monkeypatch.setattr(systemconfigreader, "read", read)
    read.return_value = PARSED_SYSTEM_CONFIG
    extra_settings = mock.MagicMock()

    systemservice.install(
        "system_id_2", "config_str", extra_settings, config_source_url=None
    )

    assert mock_systemdam.get_by_id().id == "system_id_2"

    read.assert_called_once_with("config_str", extra_settings)
    _install_feeds.assert_called_once_with(
        mock_systemdam.get_by_id(), PARSED_SYSTEM_CONFIG["feeds"]
    )
    _install_service_maps.assert_called_once_with(
        mock_systemdam.get_by_id(), PARSED_SYSTEM_CONFIG["service_maps"]
    )


def _test_install__already_exists(mock_systemdam, monkeypatch, db_session):

    monkeypatch.setattr(systemqueries, "get_by_id", mock_systemdam.get_by_id)
    monkeypatch.setattr(systemqueries, "create", mock_systemdam.create)
    system = mock_systemdam.create()
    system.status = system.SystemStatus.ACTIVE

    actual = systemservice.install(
        "system_id_2", "config_str", None, config_source_url=""
    )

    assert False is actual


def test_save_feed_configuration(monkeypatch, session_factory):
    session = session_factory()
    monkeypatch.setattr(dbconnection, "get_session", lambda: session)
    monkeypatch.setattr(
        genericqueries,
        "get_id_to_pk_map",
        lambda *args: {FEED_ID_1: FEED_PK_1, FEED_ID_2: FEED_PK_2},
    )

    system = models.System()

    feeds_config = {
        FEED_ID_2: {
            "parser": {"built_in": "GTFS_STATIC"},
            "http": {"url": "https://demo.transiter.io", "headers": {}, "timeout": 40},
            "auto_update": {"period": None, "enabled": False},
            "required_for_install": True,
        },
        FEED_ID_3: {
            "parser": {"custom": "a:b"},
            "http": {"url": "https://nytimes.com", "headers": {"key": "value"}},
            "auto_update": {"period": 5, "enabled": True},
            "required_for_install": False,
        },
    }

    expected_feed_1 = models.Feed(
        pk=FEED_PK_2,
        id=FEED_ID_2,
        built_in_parser="GTFS_STATIC",
        custom_parser=None,
        url="https://demo.transiter.io",
        headers="{}",
        http_timeout=40,
        parser_options=None,
        auto_update_enabled=False,
        auto_update_period=None,
        required_for_install=True,
    )
    expected_feed_2 = models.Feed(
        id=FEED_ID_3,
        built_in_parser=None,
        custom_parser="a:b",
        url="https://nytimes.com",
        headers=json.dumps({"key": "value"}, indent=2),
        parser_options=None,
        auto_update_period=5,
        auto_update_enabled=True,
        required_for_install=False,
    )

    feed_ids_to_update, feed_ids_to_delete = systemservice._save_feed_configuration(
        system, feeds_config
    )

    assert feed_ids_to_update == [FEED_ID_2]
    assert feed_ids_to_delete == [FEED_ID_1]
    assert [expected_feed_1, expected_feed_2] == session.merged


SERVICE_MAP_ID_1 = "101"
SERVICE_MAP_PK_1 = 102
SERVICE_MAP_ID_2 = "103"
SERVICE_MAP_PK_2 = 104
SERVICE_MAP_ID_3 = "105"


def test_save_service_map_configuration(monkeypatch, session_factory):
    session = session_factory()
    monkeypatch.setattr(dbconnection, "get_session", lambda: session)

    existing_map_1 = models.ServiceMapGroup(pk=SERVICE_MAP_PK_1, id=SERVICE_MAP_ID_1)
    existing_map_2 = models.ServiceMapGroup(
        pk=SERVICE_MAP_PK_2, id=SERVICE_MAP_ID_2, conditions="{'key': 'value2'}"
    )
    system = models.System(service_map_groups=[existing_map_1, existing_map_2])

    service_maps_config = {
        SERVICE_MAP_ID_2: {
            "source": models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
            "threshold": 0.2,
            "use_for_routes_at_stop": False,
            "use_for_stops_in_route": True,
        },
        SERVICE_MAP_ID_3: {
            "source": models.ServiceMapGroup.ServiceMapSource.REALTIME,
            "threshold": 0.3,
            "use_for_routes_at_stop": True,
            "use_for_stops_in_route": False,
            "conditions": {"key": "value"},
        },
    }

    expected_map_1 = models.ServiceMapGroup(
        pk=SERVICE_MAP_PK_2,
        id=SERVICE_MAP_ID_2,
        conditions=None,
        source=models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
        threshold=0.2,
        use_for_routes_at_stop=False,
        use_for_stops_in_route=True,
    )
    conditions = "{\n" '  "key": "value"\n' "}"
    expected_map_2 = models.ServiceMapGroup(
        id=SERVICE_MAP_ID_3,
        conditions=conditions,
        source=models.ServiceMapGroup.ServiceMapSource.REALTIME,
        threshold=0.3,
        use_for_routes_at_stop=True,
        use_for_stops_in_route=False,
    )

    systemservice._save_service_map_configuration(system, service_maps_config)

    assert [expected_map_1, expected_map_2] == session.merged
    assert [existing_map_1] == session.deleted


def test_delete__async_case(mock_systemdam, monkeypatch):
    monkeypatch.setattr(uuid, "uuid4", lambda: "uuid")
    monkeypatch.setattr(
        systemservice, "_complete_delete_operation_async", mock.MagicMock()
    )

    system = models.System(id=SYSTEM_ID)
    mock_systemdam.create(system)

    systemservice.delete_by_id(SYSTEM_ID, sync=False)

    assert system.status is models.System.SystemStatus.DELETING
    assert system.id == SYSTEM_ID + "_deleting_uuid"


def test_delete__not_exists__error(mock_systemdam):
    with pytest.raises(exceptions.IdNotFoundError):
        systemservice.delete_by_id(SYSTEM_ID, sync=False)


def test_delete__not_exists__no_error(mock_systemdam):
    systemservice.delete_by_id(SYSTEM_ID, error_if_not_exists=False, sync=False)


def test_delete__regular_case(mock_systemdam, monkeypatch):
    create_feed_flush = mock.MagicMock()
    monkeypatch.setattr(updatemanager, "create_feed_flush", create_feed_flush)
    monkeypatch.setattr(updatemanager, "execute_feed_update", mock.MagicMock())
    delete_in_system_by_id = mock.MagicMock()
    monkeypatch.setattr(feedqueries, "delete_in_system_by_id", delete_in_system_by_id)

    system = models.System(id=SYSTEM_ID)
    system.feeds = [models.Feed(id=FEED_ID_1)]
    mock_systemdam.create(system)

    systemservice.delete_by_id(SYSTEM_ID)

    assert mock_systemdam.get_by_id(SYSTEM_ID) is None
    create_feed_flush.assert_called_once_with(SYSTEM_ID, FEED_ID_1)
    delete_in_system_by_id.assert_called_once_with(SYSTEM_ID, FEED_ID_1)
