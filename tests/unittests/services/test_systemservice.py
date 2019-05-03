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
    SYSTEM_CONFIG_STR = "Blah blah blah"
    DIRECTION_NAME_ONE = "Uptown"

    def setUp(self):
        self.systemdam = self.mockImportedModule(systemservice.systemdam)
        self.updatemanager = self.mockImportedModule(systemservice.updatemanager)
        self.stopdam = self.mockImportedModule(systemservice.stopdam)

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

    @mock.patch.object(systemservice, "_SystemConfig")
    @mock.patch.object(systemservice, "_install_service_maps")
    @mock.patch.object(systemservice, "_install_feeds")
    @mock.patch.object(systemservice, "_install_direction_names")
    def test_install_success(self, step1, step2, step3, _SystemConfig):
        """[System service] Successfully install a system"""
        self.systemdam.get_by_id.return_value = None
        self.systemdam.create.return_value = self.system_1
        system_config = mock.MagicMock()
        _SystemConfig.return_value = system_config
        extra_files = mock.MagicMock()
        extra_settings = mock.MagicMock()

        actual = systemservice.install(
            self.SYSTEM_TWO_ID, self.SYSTEM_CONFIG_STR, extra_files, extra_settings
        )

        self.assertEqual(actual, True)
        self.assertEqual(self.system_1.id, self.SYSTEM_TWO_ID)

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_TWO_ID)
        self.systemdam.create.assert_called_once_with()
        _SystemConfig.assert_called_once_with(
            self.SYSTEM_CONFIG_STR, extra_files, extra_settings
        )
        step1.assert_called_once_with(self.system_1, system_config)
        step2.assert_called_once_with(self.system_1, system_config)
        step3.assert_called_once_with(self.system_1, system_config)

    def test_install_already_exists(self):
        """[System service] Fail to install because system id already taken"""
        self.systemdam.get_by_id.return_value = self.system_1

        actual = systemservice.install(self.SYSTEM_ONE_ID, "", {}, {})

        self.assertFalse(actual)

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_delete_success(self):
        """[System service] Successfully delete a system"""
        self.systemdam.delete_by_id.return_value = True

        actual = systemservice.delete_by_id(self.SYSTEM_ONE_ID)

        self.assertEqual(actual, True)
        self.systemdam.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_delete_failure(self):
        """[System service] Fail to delete a nonexistent system"""
        self.systemdam.delete_by_id.return_value = False

        self.assertRaises(
            exceptions.IdNotFoundError, systemservice.delete_by_id, self.SYSTEM_ONE_ID
        )

        self.systemdam.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_populate_system_config__feeds(self):
        """[System service] Populate feeds config"""
        feed_one_raw_url = "1001{api_key}"
        api_key = "asfhtghfgah"
        extra_settings = {"api_key": api_key}
        file_name = "File1"
        file_upload = mock.MagicMock()
        extra_files = {file_name: file_upload}

        feed_one = models.Feed()
        feed_one.id = "1000"
        feed_one.url = feed_one_raw_url.format(api_key=api_key)
        feed_one.built_in_parser = feed_one.BuiltInParser.GTFS_REALTIME
        feed_one.auto_update_on = False

        feed_two = models.Feed()
        feed_two.id = "200"
        feed_two.url = "BlahBlah"
        feed_two.custom_parser = "asdfg"
        feed_two.auto_update_on = True
        feed_two.auto_update_period = 300

        config_str = f"""
        
        [feeds]
        
            [feeds.{feed_one.id}]
            url = '{feed_one_raw_url}'
            built_in_parser = '{feed_one.built_in_parser.name}'
        
            [feeds.{feed_two.id}]
            url = '{feed_two.url}'
            custom_parser = '{feed_two.custom_parser}'
            auto_update = true
            auto_update_period = '{feed_two.auto_update_period} seconds'
            required_for_install = true
            file_upload_fallback = '{file_name}'
        
        """

        system_config = systemservice._SystemConfig(
            config_str, extra_files, extra_settings
        )

        self.assertEqual(len(system_config.feeds), 2)

        feed_config_one = system_config.feeds[0]
        self.assertEqual(feed_one, feed_config_one.feed)
        self.assertFalse(feed_config_one.required_for_install)
        self.assertIsNone(feed_config_one.file_upload_fallback)

        feed_config_two = system_config.feeds[1]
        self.assertEqual(feed_two, feed_config_two.feed)
        self.assertTrue(feed_config_two.required_for_install)
        self.assertEqual(file_upload, feed_config_two.file_upload_fallback)

    def test_populate_system_config__service_maps(self):
        """[System service] Populate service maps config"""
        service_map_group = models.ServiceMapGroup()
        service_map_group.id = "daytime"
        service_map_group.conditions = '{"weekday": true}'
        service_map_group.source = service_map_group.ServiceMapSource.REALTIME
        service_map_group.threshold = 0.1
        service_map_group.use_for_stops_in_route = False
        service_map_group.use_for_routes_at_stop = True

        config_str = f"""
        [service_maps]
        
            [service_maps.{service_map_group.id}]  
            conditions = {{weekday = true}}
            source = 'REALTIME'
            threshold = {service_map_group.threshold}
            use_for_routes_at_stop = true
        """

        system_config = systemservice._SystemConfig(config_str, {}, {})

        self.assertEqual(1, len(system_config.service_maps))
        self.assertEqual(
            service_map_group, system_config.service_maps[0].service_map_group
        )

    def test_populate_system_config__direction_names(self):
        """[System service] Populate direction names maps config"""
        file_name_one = "File1"
        file_name_two = "File2"
        file_upload_one = mock.MagicMock()
        file_upload_two = mock.MagicMock()
        extra_files = {file_name_one: file_upload_one, file_name_two: file_upload_two}

        config_str = f"""
        [direction_names]

        file_uploads = [
            '{file_name_one}',
            '{file_name_two}'
        ]
        """

        system_config = systemservice._SystemConfig(config_str, extra_files, {})

        self.assertEqual(
            [file_upload_one, file_upload_two], system_config.direction_name_files
        )

    @mock.patch.object(systemservice, "importlib")
    def test_populate_system_config__missing_packages(self, importlib):
        """[System service] Missing packages referenced in system config"""

        importlib.util.find_spec.return_value = None
        package_name = "apscheduler"

        config_str = f"""
        
        [prerequisites]
        
            packages = ['{package_name}']
            
        """

        self.assertRaises(
            systemservice._SystemConfig.InvalidSystemConfig,
            lambda: systemservice._SystemConfig(config_str, {}, {}),
        )

        importlib.util.find_spec.assert_called_once_with(package_name)

    def test_populate_system_config__missing_settings(self):
        """[System service] Missing settings in system config"""

        setting_key_one = "Blah"
        setting_key_two = "BlahTo"

        config_str = f"""
        
        [prerequisites]
        
            settings = ['{setting_key_one}', '{setting_key_two}']

        """

        self.assertRaises(
            systemservice._SystemConfig.InvalidSystemConfig,
            lambda: systemservice._SystemConfig(
                config_str, {}, {setting_key_one: "Value"}
            ),
        )

    def test_install_service_maps(self):
        """[System service] Install service maps"""
        system = models.System()
        system_config = mock.MagicMock()
        service_map_group = models.ServiceMapGroup()
        service_map_config = mock.MagicMock()
        service_map_config.service_map_group = service_map_group
        system_config.service_maps = [service_map_config]

        systemservice._install_service_maps(system, system_config)

        self.assertEqual(system, service_map_group.system)

    def test_install_feeds__not_required(self):
        """[System service] Install feed - not required for install"""
        system = models.System()
        feed_config = mock.MagicMock()
        feed_config.feed = models.Feed()
        feed_config.required_for_install = False
        system_config = mock.MagicMock()
        system_config.feeds = [feed_config]

        systemservice._install_feeds(system, system_config)

        self.assertEqual(system, feed_config.feed.system)

        self.updatemanager.assert_not_called()

    def test_install_feeds__required(self):
        """[System service] Install feed - required for install"""
        system = models.System()
        feed_config = mock.MagicMock()
        feed_config.feed = models.Feed()
        feed_config.required_for_install = True
        feed_config.file_upload_fallback = None
        system_config = mock.MagicMock()
        system_config.feeds = [feed_config]

        def execute_feed_update(feed_update):
            feed_update.status = models.FeedUpdate.Status.SUCCESS

        self.updatemanager.execute_feed_update.side_effect = execute_feed_update

        systemservice._install_feeds(system, system_config)

        self.assertEqual(system, feed_config.feed.system)

        self.updatemanager.execute_feed_update.assert_called_once()

    def test_install_feeds__required_with_fallback(self):
        """[System service] Install feed - file upload fallback used"""
        system = models.System()
        feed_config = mock.MagicMock()
        feed_config.feed = models.Feed()
        feed_config.required_for_install = True
        feed_config.file_upload_fallback = mock.MagicMock()
        system_config = mock.MagicMock()
        system_config.feeds = [feed_config]

        def execute_feed_update(feed_update, file_upload_fallback=None, cache=[]):
            if len(cache) == 0:
                cache.append(0)
                feed_update.status = models.FeedUpdate.Status.FAILURE
            else:
                assert file_upload_fallback is not None
                feed_update.status = models.FeedUpdate.Status.SUCCESS

        self.updatemanager.execute_feed_update.side_effect = execute_feed_update

        systemservice._install_feeds(system, system_config)

        self.assertEqual(system, feed_config.feed.system)

        self.assertEqual(2, self.updatemanager.execute_feed_update.call_count)

    def test_install_feeds__failed_to_update(self):
        """[System service] Install feed - failed to update"""
        for file_upload_fallback in [None, mock.MagicMock()]:
            system = models.System()
            feed_config = mock.MagicMock()
            feed_config.feed = models.Feed()
            feed_config.required_for_install = True
            feed_config.file_upload_fallback = file_upload_fallback
            system_config = mock.MagicMock()
            system_config.feeds = [feed_config]

            def execute_feed_update(feed_update, unused=None):
                feed_update.status = models.FeedUpdate.Status.FAILURE

            self.updatemanager.execute_feed_update.side_effect = execute_feed_update

            self.assertRaises(
                exceptions.InstallError,
                lambda: systemservice._install_feeds(system, system_config),
            )

        self.assertEqual(1 + 2, self.updatemanager.execute_feed_update.call_count)

    def test_import_static_data__direction_names(self):
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

        direction_name_rule = models.DirectionNameRule()
        direction_name_rule.priority = 0
        direction_name_rule.direction_id = True
        direction_name_rule.track = None
        direction_name_rule.name = self.DIRECTION_NAME_ONE

        systemservice._install_direction_names(system, system_config)

        self.assertEqual([direction_name_rule], stop_one.direction_name_rules)
