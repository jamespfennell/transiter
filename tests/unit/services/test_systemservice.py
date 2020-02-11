import unittest
import unittest.mock as mock

from transiter.services import systemservice, links
from transiter import models, exceptions
from .. import testutil


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
        self.system_1.id = self.SYSTEM_ONE_ID
        self.system_2 = models.System()
        self.system_2.id = self.SYSTEM_TWO_ID

    def test_list_all(self):
        """[System service] List all installed systems"""
        expected = [
            {
                **self.system_1.short_repr(),
                "href": links.SystemEntityLink(self.system_1),
            },
            {
                **self.system_2.short_repr(),
                "href": links.SystemEntityLink(self.system_2),
            },
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
        expected.update(**self.system_1.short_repr())
        expected["agency_alerts"] = [alert.long_repr()]

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

    @mock.patch.object(systemservice.systemconfigreader, "read")
    @mock.patch.object(systemservice, "_install_service_maps")
    @mock.patch.object(systemservice, "_install_feeds")
    def test_install_success(self, _install_feeds, _install_service_maps, read):
        """[System service] Successfully install a system"""

        self.systemdam.get_by_id.return_value = None
        self.systemdam.create.return_value = self.system_1
        read.return_value = self.SYSTEM_CONFIG_STR
        extra_settings = mock.MagicMock()

        actual = systemservice.install(
            self.SYSTEM_TWO_ID, self.SYSTEM_CONFIG_STR, extra_settings
        )

        self.assertEqual(actual, True)
        self.assertEqual(self.system_1.id, self.SYSTEM_TWO_ID)

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_TWO_ID)
        self.systemdam.create.assert_called_once_with()
        read.assert_called_once_with(self.SYSTEM_CONFIG_STR, extra_settings)
        _install_feeds.assert_called_once_with(
            self.system_1, self.SYSTEM_CONFIG_STR["feeds"]
        )
        _install_service_maps.assert_called_once_with(
            self.system_1, self.SYSTEM_CONFIG_STR["service_maps"]
        )

    def test_install_already_exists(self):
        """[System service] Fail to install because system id already taken"""
        self.systemdam.get_by_id.return_value = self.system_1

        actual = systemservice.install(self.SYSTEM_ONE_ID, "", {})

        self.assertFalse(actual)

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

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

    def __import_static_data__direction_names(self):
        """[System service] Install direction names"""
        system = models.System()
        stop_one = models.Stop()
        stop_one.id = self.STOP_ONE_ID
        self.stopdam.list_all_in_system.return_value = [stop_one]

        file = mock.MagicMock()
        system_config = mock.MagicMock()
        system_config.direction_name_files = [file]
        file.readlines.return_value = (
            s.encode("utf-8")
            for s in [
                "stop_id,direction_id,direction_name",
                "{},0,{}".format(self.STOP_ONE_ID, self.DIRECTION_NAME_ONE),
                "{},1,{}".format("Unknown", self.DIRECTION_NAME_ONE),
            ]
        )

        direction_name_rule = models.DirectionRule()
        direction_name_rule.priority = 0
        direction_name_rule.direction_id = True
        direction_name_rule.track = None
        direction_name_rule.name = self.DIRECTION_NAME_ONE

        systemservice._install_direction_rules(system, system_config)

        self.assertEqual([direction_name_rule], stop_one.direction_rules)
