import unittest
import unittest.mock as mock

from transiter.services import systemservice
from transiter.general import exceptions
from transiter import models
from .. import testutil


class TestSystemService(testutil.TestCase(systemservice), unittest.TestCase):

    SYSTEM_ONE_ID = '1'
    SYSTEM_TWO_ID = '2'
    SYSTEM_TWO_HREF = '4'
    SYSTEM_TWO_REPR = {'system_id': SYSTEM_TWO_ID, 'href': SYSTEM_TWO_HREF}
    SYSTEM_ONE_NUM_STOPS = 20
    SYSTEM_ONE_NUM_STATIONS = 21
    SYSTEM_ONE_NUM_ROUTES = 22
    SYSTEM_ONE_NUM_FEEDS = 23
    FILE_NAME = '24'
    SYSTEM_CONFIG_STR = 'Blah blah blah'

    def setUp(self):
        self.systemdam = self.mockImportedModule(systemservice.systemdam)

        self.system_1 = models.System()
        self.system_1.id = self.SYSTEM_ONE_ID
        self.system_2 = models.System()
        self.system_2.id = self.SYSTEM_TWO_ID

    def test_list_all(self):
        """[System service] List all installed systems"""
        expected = [
            {
                **self.system_1.short_repr(),
                'href': systemservice.linksutil.SystemEntityLink(self.system_1)
            },
            {
                **self.system_2.short_repr(),
                'href': systemservice.linksutil.SystemEntityLink(self.system_2)
            }
        ]
        self.systemdam.list_all.return_value = [
            self.system_1,
            self.system_2
        ]

        actual = systemservice.list_all(True)

        self.assertEqual(actual, expected)
        self.systemdam.list_all.assert_called_once()

    def test_get_by_id_no_such_system(self):
        """[System service] Get a non-existent system"""
        self.systemdam.get_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            systemservice.get_by_id,
            self.SYSTEM_ONE_ID
        )

    def test_get_by_id(self):
        """[System service] Get a specific system"""

        hrefs_dict = {
            'stops': systemservice.linksutil.StopsInSystemIndexLink(self.system_1),
            'routes': systemservice.linksutil.RoutesInSystemIndexLink(self.system_1),
            'feeds': systemservice.linksutil.FeedsInSystemIndexLink(self.system_1),
        }
        child_entities_dict = {
            'stops': self.SYSTEM_ONE_NUM_STOPS,
            'routes': self.SYSTEM_ONE_NUM_ROUTES,
            'feeds': self.SYSTEM_ONE_NUM_FEEDS
        }
        expected = {
            name: {
                'count': count,
                'href': hrefs_dict[name]
            } for (name, count) in child_entities_dict.items()
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
        self.systemdam.count_routes_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)
        self.systemdam.count_feeds_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)

    @mock.patch.object(systemservice, '_SystemConfig')
    @mock.patch.object(systemservice, '_install_service_maps')
    @mock.patch.object(systemservice, '_install_feeds')
    @mock.patch.object(systemservice, '_install_direction_names')
    def test_install_success(self, step1, step2, step3, _SystemConfig):
        """[System service] Successfully install a system"""
        self.systemdam.get_by_id.return_value = None
        self.systemdam.create.return_value = self.system_1
        system_config = mock.MagicMock()
        _SystemConfig.return_value = system_config
        extra_files = mock.MagicMock()
        extra_settings = mock.MagicMock()

        actual = systemservice.install(
            self.SYSTEM_TWO_ID, self.SYSTEM_CONFIG_STR, extra_files, extra_settings)

        self.assertEqual(actual, True)
        self.assertEqual(self.system_1.id, self.SYSTEM_TWO_ID)

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_TWO_ID)
        self.systemdam.create.assert_called_once_with()
        _SystemConfig.assert_called_once_with(self.SYSTEM_CONFIG_STR, extra_files, extra_settings)
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

        self.assertRaises(exceptions.IdNotFoundError,
                          systemservice.delete_by_id,
                          self.SYSTEM_ONE_ID)

        self.systemdam.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    def test_populate_system_config__feeds(self):
        """[System service] Populate feeds config"""
        feed_one_raw_url = '1001{api_key}'
        api_key = 'asfhtghfgah'
        extra_settings = {
            'api_key': api_key
        }
        file_name = 'File1'
        file_upload = mock.MagicMock()
        extra_files = {
            file_name: file_upload
        }

        feed_one = models.Feed()
        feed_one.id = '1000'
        feed_one.url = feed_one_raw_url.format(api_key=api_key)
        feed_one.parser = '1231435'
        feed_one.auto_updater_enabled = False

        feed_two = models.Feed()
        feed_two.id = '200'
        feed_two.url = 'BlahBlah'
        feed_two.parser = 'asdfg'
        feed_two.auto_updater_enabled = True
        feed_two.auto_updater_frequency = 300

        config_str = f"""
        
        [feeds]
        
            [feeds.{feed_one.id}]
            url = '{feed_one_raw_url}'
            parser = '{feed_one.parser}'
        
            [feeds.{feed_two.id}]
            url = '{feed_two.url}'
            parser = '{feed_two.parser}'
            auto_update = true
            auto_update_period = '{feed_two.auto_updater_frequency} seconds'
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
        service_map_group.id = 'daytime'
        service_map_group.conditions = '{"weekday": true}'
        service_map_group.source = 'realtime'
        service_map_group.threshold = 0.1
        service_map_group.use_for_stops_in_route = False
        service_map_group.use_for_routes_at_stop = True

        config_str = f"""
        [service_maps]
        
            [service_maps.{service_map_group.id}]  
            conditions = {{weekday = true}}
            source = 'realtime'
            threshold = {service_map_group.threshold}
            use_for_routes_at_stop = true
        """

        system_config = systemservice._SystemConfig(
            config_str, {}, {}
        )

        self.assertEqual(1, len(system_config.service_maps))
        self.assertEqual(
            service_map_group,
            system_config.service_maps[0].service_map_group
        )

    def test_populate_system_config__direction_names(self):
        """[System service] Populate direction names maps config"""
        file_name_one = 'File1'
        file_name_two = 'File2'
        file_upload_one = mock.MagicMock()
        file_upload_two = mock.MagicMock()
        extra_files = {
            file_name_one: file_upload_one,
            file_name_two: file_upload_two
        }

        config_str = f"""
        [direction_names]

        file_uploads = [
            '{file_name_one}',
            '{file_name_two}'
        ]
        """

        system_config = systemservice._SystemConfig(
            config_str, extra_files, {}
        )

        self.assertEqual(
            [file_upload_one, file_upload_two],
            system_config.direction_name_files
        )

    @mock.patch.object(systemservice, 'importlib')
    def test_populate_system_config__missing_packages(self, importlib):
        """[System service] Missing packages referenced in system config"""

        importlib.util.find_spec.return_value = None
        package_name = 'apscheduler'

        config_str = f"""
        
        [prerequisites]
        
            packages = ['{package_name}']
            
        """

        self.assertRaises(
            systemservice._SystemConfig.InvalidSystemConfig,
            lambda: systemservice._SystemConfig(
                config_str, {}, {}
            )
        )

        importlib.util.find_spec.assert_called_once_with(package_name)

    def test_populate_system_config__missing_settings(self):
        """[System service] Missing settings in system config"""

        setting_key_one = 'Blah'
        setting_key_two = 'BlahTo'

        config_str = f"""
        
        [prerequisites]
        
            settings = ['{setting_key_one}', '{setting_key_two}']

        """

        self.assertRaises(
            systemservice._SystemConfig.InvalidSystemConfig,
            lambda: systemservice._SystemConfig(
                config_str, {}, {setting_key_one: 'Value'}
            )
        )


class _TestImportStaticData(unittest.TestCase):

    SYSTEM_ID = '1'
    STOP_ONE_ID = '2'
    STOP_TWO_ID = '3'
    STOP_ONE_ID_ALIAS = '4'
    FEED_NAME = '10'
    FEED_URL = '11'
    FEED_PARSER_MODULE = '12'
    FEED_PARSER_FUNCTION = '13'

    def _quick_mock(self, name):
        cache_name = '_quick_mock_cache_{}'.format(name)
        self.__setattr__(cache_name, mock.patch(
            'transiter.services.systemservice.{}'.format(name)))
        mocked = getattr(self, cache_name).start()
        self.addCleanup(getattr(self, cache_name).stop)
        return mocked

    def setUp(self):
        self._quick_mock('servicepatternmanager')
        importlib = self._quick_mock('importlib')
        package = mock.MagicMock()
        importlib.import_module.return_value = package
        package.__file__ = ''

        GtfsStaticParser = self._quick_mock('gtfsstaticutil.GtfsStaticParser')
        self.gtfs_static_parser = mock.MagicMock()
        GtfsStaticParser.return_value = self.gtfs_static_parser

        self.gtfs_static_parser.route_id_to_route = {}
        self.gtfs_static_parser.stop_id_to_stop = {}
        self.gtfs_static_parser.transfer_tuples = []
        self.gtfs_static_parser.stop_id_alias_to_stop_alias = {}

        SystemConfig = self._quick_mock('SystemConfig')
        self.system_config = mock.MagicMock()
        SystemConfig.return_value = self.system_config
        self.system_config.direction_name_rules_files = []
        self.system_config.feeds = []

        self.system = models.System()
        self.system.system_id = self.SYSTEM_ID

    def test_import_static_data__routes(self):
        route = models.Route()
        self.gtfs_static_parser.route_id_to_route = {'route': route}

        systemservice._import_static_data(self.system)

        self.assertEqual(route.system, self.system)

    def test_import_static_data__stops(self):

        stop_one = models.Stop()
        stop_one.id = self.STOP_ONE_ID
        stop_one.parent_stop_id = None
        stop_two = models.Stop()
        stop_two.id = self.STOP_TWO_ID
        stop_two.parent_stop_id = None
        self.gtfs_static_parser.stop_id_to_stop = {
            self.STOP_ONE_ID: stop_one,
            self.STOP_TWO_ID: stop_two
        }

        systemservice._import_static_data(self.system)

        self.assertEqual(stop_one.system, self.system)
        self.assertEqual(stop_two.system, self.system)
        self.assertEqual(2, len(self.system.stops))

    @mock.patch('transiter.services.systemservice._lift_stop_properties')
    def test_import_static_data__stops_with_transfer(self, __):

        stop_one = models.Stop()
        stop_one.id = self.STOP_ONE_ID
        stop_one.parent_stop_id = None
        stop_two = models.Stop()
        stop_two.id = self.STOP_TWO_ID
        stop_two.parent_stop_id = None
        self.gtfs_static_parser.stop_id_to_stop = {
            self.STOP_ONE_ID: stop_one,
            self.STOP_TWO_ID: stop_two
        }

        self.gtfs_static_parser.transfer_tuples = [
            (self.STOP_ONE_ID, self.STOP_TWO_ID)]

        systemservice._import_static_data(self.system)

        self.assertEqual(stop_one.system, self.system)
        self.assertEqual(stop_two.system, self.system)
        self.assertEqual(3, len(self.system.stops))
        self.assertDictEqual(
            self.gtfs_static_parser.stop_id_to_stop,
            {stop.id: stop for stop in stop_one.parent_stop.child_stops})

    def test_import_static_data__feeds(self):
        feed_config = [{
            'name': self.FEED_NAME,
            'url': self.FEED_URL,
            'parser': 'custom',
            'custom_parser': {
                'module': self.FEED_PARSER_MODULE,
                'function': self.FEED_PARSER_FUNCTION
            }
        }]
        self.system_config.feeds = feed_config
        feed = models.Feed()
        feed.id = self.FEED_NAME
        feed.url = self.FEED_URL
        feed.parser = 'custom'
        feed.custom_module = self.FEED_PARSER_MODULE
        feed.custom_function = self.FEED_PARSER_FUNCTION
        feed.auto_updater_enabled = True
        feed.auto_updater_frequency = 5

        systemservice._import_static_data(self.system)

        self.assertEqual([feed], self.system.feeds)

    FILE_NAME = '20'
    DIRECTION_NAME = '21'

    @mock.patch('transiter.services.systemservice.open')
    @mock.patch('transiter.services.systemservice.csv')
    def test_import_static_data__direction_names(self, csv, open):
        stop_one = models.Stop()
        stop_one.id = self.STOP_ONE_ID
        stop_one.parent_stop_id = None
        self.gtfs_static_parser.stop_id_to_stop = {
            self.STOP_ONE_ID: stop_one,
        }

        self.system_config.direction_name_rules_files = [self.FILE_NAME]
        csv_file = mock.MagicMock()

        open.return_value = ContextManager(csv_file)
        csv.DictReader.return_value = [
            {
                'stop_id': self.STOP_ONE_ID,
                'direction_id': '0',
                'direction_name': self.DIRECTION_NAME
            },
            {
                'stop_id': self.STOP_TWO_ID
            }
        ]

        direction_name_rule = models.DirectionNameRule()
        direction_name_rule.priority = 0
        direction_name_rule.direction_id = True
        direction_name_rule.track = None
        direction_name_rule.stop_id_alias = None
        direction_name_rule.name = self.DIRECTION_NAME

        systemservice._import_static_data(self.system)

        self.assertEqual([direction_name_rule], stop_one.direction_name_rules)



# TODO: put this in shared test module
class ContextManager(object):
    def __init__(self, dummy_resource=None):
        self.dummy_resource = dummy_resource

    def __enter__(self):
        return self.dummy_resource

    def __exit__(self, *args):
        pass