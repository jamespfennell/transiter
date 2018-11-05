import unittest
import unittest.mock as mock

from transiter.services import systemservice
from transiter.services import exceptions
from transiter.database import models

class TestSystemService(unittest.TestCase):

    SYSTEM_ONE_ID = '1'
    SYSTEM_ONE_HREF = '3'
    SYSTEM_ONE_REPR = {'system_id': SYSTEM_ONE_ID, 'href': SYSTEM_ONE_HREF}
    SYSTEM_TWO_ID = '2'
    SYSTEM_TWO_HREF = '4'
    SYSTEM_TWO_REPR = {'system_id': SYSTEM_TWO_ID, 'href': SYSTEM_TWO_HREF}
    SYSTEM_ONE_NUM_STOPS = 20
    SYSTEM_ONE_NUM_STATIONS = 21
    SYSTEM_ONE_NUM_ROUTES = 22
    SYSTEM_ONE_NUM_FEEDS = 23
    FILE_NAME = '24'

    @classmethod
    def setUp(cls):
        cls.system_1 = mock.MagicMock()
        cls.system_1.short_repr.return_value = cls.SYSTEM_ONE_REPR.copy()
        cls.system_2 = mock.MagicMock()
        cls.system_2.short_repr.return_value = cls.SYSTEM_TWO_REPR.copy()

    @mock.patch('transiter.services.systemservice.linksutil')
    @mock.patch('transiter.services.systemservice.system_dao')
    def test_list_all(self, system_dao, linksutil):
        """[System service] List all installed systems"""

        def SystemEntityLink(system):
            if system == self.system_1:
                return self.SYSTEM_ONE_HREF
            if system == self.system_2:
                return self.SYSTEM_TWO_HREF
        linksutil.SystemEntityLink.side_effect = SystemEntityLink

        expected = [self.SYSTEM_ONE_REPR, self.SYSTEM_TWO_REPR]
        system_dao.list_all.return_value = [
            self.system_1,
            self.system_2]

        actual = systemservice.list_all()

        self.assertEqual(actual, expected)
        system_dao.list_all.assert_called_once()
        self.system_1.short_repr.assert_called_once()
        self.system_2.short_repr.assert_called_once()

    @mock.patch('transiter.services.systemservice.linksutil')
    @mock.patch('transiter.services.systemservice.system_dao')
    def test_get_by_id(self, system_dao, linksutil):
        """[System service] Get a specific system"""

        hrefs_dict = {
            'stops': 'href1',
            'stations': 'NI',
            'routes': 'href3',
            'feeds': 'href4'
        }
        child_entities_dict = {
            'stops': self.SYSTEM_ONE_NUM_STOPS,
            'stations': self.SYSTEM_ONE_NUM_STATIONS,
            'routes': self.SYSTEM_ONE_NUM_ROUTES,
            'feeds': self.SYSTEM_ONE_NUM_FEEDS
        }
        expected = {
            name: {
                'count': count,
                'href': hrefs_dict[name]
            } for (name, count) in child_entities_dict.items()
        }
        expected.update(**self.SYSTEM_ONE_REPR)

        system_dao.get_by_id.return_value = self.system_1
        system_dao.count_stops_in_system.return_value = self.SYSTEM_ONE_NUM_STOPS
        system_dao.count_stations_in_system.return_value = self.SYSTEM_ONE_NUM_STATIONS
        system_dao.count_routes_in_system.return_value = self.SYSTEM_ONE_NUM_ROUTES
        system_dao.count_feeds_in_system.return_value = self.SYSTEM_ONE_NUM_FEEDS

        linksutil.StopsInSystemIndexLink.return_value = hrefs_dict['stops']
        linksutil.RoutesInSystemIndexLink.return_value = hrefs_dict['routes']
        linksutil.FeedsInSystemIndexLink.return_value = hrefs_dict['feeds']

        actual = systemservice.get_by_id(self.SYSTEM_ONE_ID)

        self.maxDiff = None
        self.assertDictEqual(actual, expected)
        system_dao.get_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)
        self.system_1.short_repr.assert_called_once()
        system_dao.count_stops_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)
        system_dao.count_stations_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)
        system_dao.count_routes_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)
        system_dao.count_feeds_in_system.assert_called_once_with(self.SYSTEM_ONE_ID)

    @mock.patch('transiter.services.systemservice._import_static_data')
    @mock.patch('transiter.services.systemservice.system_dao')
    def test_install_success(self, system_dao, _import_static_data):
        """[System service] Successfully install a system"""
        new_system = mock.MagicMock()
        system_dao.get_by_id.return_value = None
        system_dao.create.return_value = new_system

        actual = systemservice.install(self.SYSTEM_ONE_ID)

        self.assertEqual(actual, True)
        self.assertEqual(new_system.system_id, self.SYSTEM_ONE_ID)
        system_dao.get_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)
        system_dao.create.assert_called_once_with()
        _import_static_data.assert_called_once_with(new_system)

    @mock.patch('transiter.services.systemservice.system_dao')
    def test_install_already_exists(self, system_dao):
        """[System service] Fail to install because system id already taken"""
        system_dao.get_by_id.return_value = self.system_1

        actual = systemservice.install(self.SYSTEM_ONE_ID)

        self.assertEqual(actual, False)
        system_dao.get_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    @mock.patch('transiter.services.systemservice.system_dao')
    def test_delete_success(self, system_dao):
        """[System service] Successfully delete a system"""
        system_dao.delete_by_id.return_value = True

        actual = systemservice.delete_by_id(self.SYSTEM_ONE_ID)

        self.assertEqual(actual, True)
        system_dao.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    @mock.patch('transiter.services.systemservice.system_dao')
    def test_delete_failure(self, system_dao):
        """[System service] Fail to delete a nonexistent system"""
        system_dao.delete_by_id.return_value = False

        self.assertRaises(exceptions.IdNotFoundError,
                          systemservice.delete_by_id,
                          self.SYSTEM_ONE_ID)

        system_dao.delete_by_id.assert_called_once_with(self.SYSTEM_ONE_ID)

    @mock.patch('transiter.services.systemservice.open')
    @mock.patch('transiter.services.systemservice.yaml')
    def test_system_config(self, yaml, open):
        yaml_file = mock.MagicMock()
        open.return_value = ContextManager(yaml_file)

        feeds = mock.MagicMock()
        static_route_service_patterns = mock.MagicMock()
        static_other_service_patterns = mock.MagicMock()
        realtime_route_service_patterns = mock.MagicMock()
        direction_name_rules_files = mock.MagicMock()

        yaml.load.return_value = {
            'feeds': feeds,
            'static_route_service_patterns': static_route_service_patterns,
            'static_other_service_patterns': static_other_service_patterns,
            'realtime_route_service_patterns': realtime_route_service_patterns,
            'direction_name_rules_files': direction_name_rules_files
        }

        system_config = systemservice.SystemConfig(self.FILE_NAME)

        self.assertEqual(system_config.feeds, feeds)
        open.assert_called_once_with(self.FILE_NAME, 'r')
        yaml.load.assert_called_once_with(yaml_file)


class TestImportStaticData(unittest.TestCase):

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
        stop_one.stop_id = self.STOP_ONE_ID
        stop_two = models.Stop()
        stop_two.stop_id = self.STOP_TWO_ID
        self.gtfs_static_parser.stop_id_to_stop = {
            self.STOP_ONE_ID: stop_one,
            self.STOP_TWO_ID: stop_two
        }

        systemservice._import_static_data(self.system)

        self.assertEqual(stop_one.system, self.system)
        self.assertEqual(stop_two.system, self.system)
        self.assertEqual(2, len(self.system.stations))
        self.assertEqual([stop_one], stop_one.station.stops)
        self.assertEqual([stop_two], stop_two.station.stops)

    def test_import_static_data__stops_with_transfer(self):

        stop_one = models.Stop()
        stop_one.stop_id = self.STOP_ONE_ID
        stop_two = models.Stop()
        stop_two.stop_id = self.STOP_TWO_ID
        self.gtfs_static_parser.stop_id_to_stop = {
            self.STOP_ONE_ID: stop_one,
            self.STOP_TWO_ID: stop_two
        }

        self.gtfs_static_parser.transfer_tuples = [
            (self.STOP_ONE_ID, self.STOP_TWO_ID)]

        systemservice._import_static_data(self.system)

        self.assertEqual(stop_one.system, self.system)
        self.assertEqual(stop_two.system, self.system)
        self.assertEqual(1, len(self.system.stations))
        self.assertDictEqual(
            self.gtfs_static_parser.stop_id_to_stop,
            {stop.stop_id: stop for stop in stop_one.station.stops})

    def test_import_static_data__stop_alias(self):

        stop_one = models.Stop()
        stop_one.stop_id = self.STOP_ONE_ID
        self.gtfs_static_parser.stop_id_to_stop = {
            self.STOP_ONE_ID: stop_one,
        }

        stop_one_id_alias = models.StopAlias()
        stop_one_id_alias.stop_id = self.STOP_ONE_ID
        stop_one_id_alias.stop_id_alias = self.STOP_ONE_ID_ALIAS
        self.gtfs_static_parser.stop_id_alias_to_stop_alias = {
            self.STOP_ONE_ID_ALIAS: stop_one_id_alias
        }

        systemservice._import_static_data(self.system)

        self.assertEqual([stop_one_id_alias], stop_one.stop_aliases)

    def test_import_static_data__feeds(self):
        feed_config = [{
            'name': self.FEED_NAME,
            'url': self.FEED_URL,
            'parser_module': self.FEED_PARSER_MODULE,
            'parser_function': self.FEED_PARSER_FUNCTION
        }]
        self.system_config.feeds = feed_config
        feed = models.Feed()
        feed.feed_id = self.FEED_NAME
        feed.url = self.FEED_URL
        feed.parser_module = self.FEED_PARSER_MODULE
        feed.parser_function = self.FEED_PARSER_FUNCTION

        systemservice._import_static_data(self.system)

        self.assertEqual([feed], self.system.feeds)

    FILE_NAME = '20'
    DIRECTION_NAME = '21'

    @mock.patch('transiter.services.systemservice.open')
    @mock.patch('transiter.services.systemservice.csv')
    def test_import_static_data__direction_names(self, csv, open):
        stop_one = models.Stop()
        stop_one.stop_id = self.STOP_ONE_ID
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