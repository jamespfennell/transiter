import unittest
import unittest.mock as mock

import pytest

from transiter import models, exceptions
from transiter.data.dams import systemdam
from transiter.services import systemservice, links, systemconfigreader
from .. import testutil

PARSED_SYSTEM_CONFIG = {
    "name": "Name",
    "requirements": {"packages": [], "extra_settings": {}},
    "feeds": "Blah blah blah",
    "service_maps": "ser",
    "direction_rules_files": [],
}


class TestSystemService(testutil.TestCase(systemservice), unittest.TestCase):

    SYSTEM_ONE_ID = "1"
    SYSTEM_TWO_ID = "2"
    SYSTEM_TWO_HREF = "4"
    SYSTEM_TWO_REPR = {"system_id": SYSTEM_TWO_ID, "href": SYSTEM_TWO_HREF}
    SYSTEM_ONE_NUM_STOPS = 20
    SYSTEM_ONE_NUM_STATIONS = 21
    SYSTEM_ONE_NUM_ROUTES = 22
    SYSTEM_ONE_NUM_FEEDS = 23
    FILE_NAME = "24"
    STOP_ONE_ID = "25"
    SYSTEM_CONFIG_STR = {
        "name": "Name",
        "requirements": {"packages": [], "extra_settings": {}},
        "feeds": "Blah blah blah",
        "service_maps": "ser",
        "direction_rules_files": [],
    }
    DIRECTION_NAME_ONE = "Uptown"

    def setUp(self):
        self.systemdam = self.mockImportedModule(systemservice.systemdam)
        self.feeddam = self.mockImportedModule(systemservice.feeddam)
        self.updatemanager = self.mockImportedModule(systemservice.updatemanager)

        self.system_1 = models.System()
        self.system_1.status = self.system_1.SystemStatus.ACTIVE
        self.system_1.id = self.SYSTEM_ONE_ID
        self.system_2 = models.System()
        self.system_2.status = self.system_1.SystemStatus.ACTIVE
        self.system_2.id = self.SYSTEM_TWO_ID

    def test_list_all(self):
        """[System service] List all installed systems"""
        expected = [
            {**self.system_1.to_dict(), "href": links.SystemEntityLink(self.system_1),},
            {**self.system_2.to_dict(), "href": links.SystemEntityLink(self.system_2),},
        ]
        self.systemdam.list_all.return_value = [self.system_1, self.system_2]

        actual = systemservice.list_all(True)

        self.assertEqual(actual, expected)
        self.systemdam.list_all.assert_called_once()

    def test_get_by_id_no_such_system(self):
        """[System service] Get a non-existent system"""
        self.systemdam.get_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError, systemservice.get_by_id, self.SYSTEM_ONE_ID
        )

    def test_get_by_id(self):
        """[System service] Get a specific system"""
        alert = models.Alert(id="alert_id", header="alert_header")
        self.systemdam.list_all_alerts_associated_to_system.return_value = [alert]

        hrefs_dict = {
            "stops": links.StopsInSystemIndexLink(self.system_1),
            "routes": links.RoutesInSystemIndexLink(self.system_1),
            "feeds": links.FeedsInSystemIndexLink(self.system_1),
        }
        child_entities_dict = {
            "stops": self.SYSTEM_ONE_NUM_STOPS,
            "routes": self.SYSTEM_ONE_NUM_ROUTES,
            "feeds": self.SYSTEM_ONE_NUM_FEEDS,
        }
        expected = {
            name: {"count": count, "href": hrefs_dict[name]}
            for (name, count) in child_entities_dict.items()
        }
        expected.update(**self.system_1.to_dict())
        expected["agency_alerts"] = [alert.to_large_dict()]

        self.systemdam.get_by_id.return_value = self.system_1
        self.systemdam.count_stops_in_system.return_value = self.SYSTEM_ONE_NUM_STOPS
        self.systemdam.count_routes_in_system.return_value = self.SYSTEM_ONE_NUM_ROUTES
        self.systemdam.count_feeds_in_system.return_value = self.SYSTEM_ONE_NUM_FEEDS

        actual = systemservice.get_by_id(self.SYSTEM_ONE_ID, True)

        self.maxDiff = None
        self.assertDictEqual(actual, expected)
        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)
        self.systemdam.count_stops_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)
        self.systemdam.count_routes_in_system.assert_called_once_with(
            self.SYSTEM_ONE_ID
        )
        self.systemdam.count_feeds_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_delete_success(self):
        """[System service] Successfully delete a system"""
        self.feeddam.list_all_in_system.return_value = []
        self.systemdam.delete_by_id.return_value = True

        actual = systemservice.delete_by_id(self.SYSTEM_ONE_ID)

        self.assertEqual(actual, True)
        self.systemdam.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_delete_failure(self):
        """[System service] Fail to delete a nonexistent system"""
        self.feeddam.list_all_in_system.return_value = []
        self.systemdam.delete_by_id.return_value = False

        self.assertRaises(
            exceptions.IdNotFoundError, systemservice.delete_by_id, self.SYSTEM_ONE_ID
        )

        self.systemdam.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_install_feeds__not_required(self):
        """[System service] Install feed - not required for install"""

        feeds_config = {
            "feed": {
                "parser": {"built_in": models.Feed.BuiltInParser.GTFS_REALTIME},
                "http": {"url": "URL", "headers": {}},
                "auto_update": {"enabled": True, "period": 5},
                "required_for_install": False,
            }
        }

        systemservice._install_feeds(self.system_1, feeds_config)

        self.updatemanager.assert_not_called()

    def test_install_feeds__required(self):
        """[System service] Install feed - required for install"""

        feeds_config = {
            "feed": {
                "parser": {"built_in": models.Feed.BuiltInParser.GTFS_REALTIME},
                "http": {"url": "URL", "headers": {}},
                "auto_update": {"enabled": True, "period": 5},
                "required_for_install": True,
            }
        }

        def execute_feed_update(feed_update):
            feed_update.status = models.FeedUpdate.Status.SUCCESS

        self.updatemanager.execute_feed_update.side_effect = execute_feed_update

        systemservice._install_feeds(self.system_1, feeds_config)

        self.updatemanager.execute_feed_update.assert_called_once()

    def test_install_feeds__failed_to_update(self):
        """[System service] Install feed - failed to update"""

        feeds_config = {
            "feed": {
                "parser": {"built_in": models.Feed.BuiltInParser.GTFS_REALTIME},
                "http": {"url": "URL", "headers": {}},
                "auto_update": {"enabled": True, "period": 5},
                "required_for_install": True,
            }
        }

        def execute_feed_update(feed_update, __=None):
            feed_update.status = models.FeedUpdate.Status.FAILURE

        self.updatemanager.execute_feed_update.side_effect = execute_feed_update

        self.assertRaises(
            exceptions.InstallError,
            lambda: systemservice._install_feeds(self.system_1, feeds_config),
        )

        self.updatemanager.execute_feed_update.assert_called_once()


@pytest.fixture
def mock_systemdam():
    class SystemDam:
        def __init__(self):
            self._system = None

        def get_by_id(self, *args, **kwargs):
            return self._system

        def create(self):
            self._system = models.System()
            return self._system

    return SystemDam()


def test_install(mock_systemdam, monkeypatch):

    monkeypatch.setattr(systemdam, "get_by_id", mock_systemdam.get_by_id)
    monkeypatch.setattr(systemdam, "create", mock_systemdam.create)

    _install_service_maps = mock.MagicMock()
    monkeypatch.setattr(systemservice, "_install_service_maps", _install_service_maps)
    _install_feeds = mock.MagicMock()
    monkeypatch.setattr(systemservice, "_install_feeds", _install_feeds)

    read = mock.MagicMock()
    monkeypatch.setattr(systemconfigreader, "read", read)
    read.return_value = PARSED_SYSTEM_CONFIG
    extra_settings = mock.MagicMock()

    actual = systemservice.install("system_id_2", "config_str", extra_settings)

    assert True is actual
    assert mock_systemdam.get_by_id().id == "system_id_2"

    read.assert_called_once_with("config_str", extra_settings)
    _install_feeds.assert_called_once_with(
        mock_systemdam.get_by_id(), PARSED_SYSTEM_CONFIG["feeds"]
    )
    _install_service_maps.assert_called_once_with(
        mock_systemdam.get_by_id(), PARSED_SYSTEM_CONFIG["service_maps"]
    )


def test_install__already_exists(mock_systemdam, monkeypatch):

    monkeypatch.setattr(systemdam, "get_by_id", mock_systemdam.get_by_id)
    monkeypatch.setattr(systemdam, "create", mock_systemdam.create)
    system = mock_systemdam.create()
    system.status = system.SystemStatus.ACTIVE

    actual = systemservice.install("system_id_2", "config_str", mock.MagicMock)

    assert False is actual
