import os
import unittest

from sqlalchemy.sql import text

from transiter import models, config
from transiter.data import database
from transiter.data.dams import feeddam, tripdam, systemdam, routedam, stopdam, servicepatterndam


class TestDbConstants:
    SYSTEM_ONE_PK = 8
    SYSTEM_TWO_PK = 9
    SYSTEM_ONE_ID = '1'
    SYSTEM_TWO_ID = '2'
    SYSTEM_THREE_ID = '3'
    SYSTEM_THREE_NAME = '4'
    SYSTEM_ONE_PACKAGE = '5'
    SYSTEM_TWO_PACKAGE = '6'
    SYSTEM_THREE_PACKAGE = '7'

    ROUTE_ONE_ID = '11'
    ROUTE_ONE_PK = 12
    ROUTE_TWO_ID = '13'
    ROUTE_TWO_PK = 14
    ROUTE_THREE_ID = '15'
    ROUTE_THREE_PK = 16

    TRIP_ONE_ID = '21'
    TRIP_ONE_PK = 22
    TRIP_TWO_ID = '23'
    TRIP_TWO_PK = 24
    TRIP_THREE_ID = '25'
    TRIP_THREE_PK = 26

    STOP_ONE_ID = '41'
    STOP_ONE_PK = 42
    STOP_TWO_ID = '43'
    STOP_TWO_PK = 44
    STOP_THREE_ID = '45'
    STOP_THREE_PK = 46
    STOP_FOUR_ID = '47'
    STOP_FOUR_PK = 48
    STOP_FIVE_ID = '49'
    STOP_FIVE_PK = 50

    FEED_ONE_ID = '71'
    FEED_ONE_PK = 72
    FEED_TWO_ID = '73'
    FEED_TWO_PK = 74

    ROUTE_STATUS_ONE_PK = 81
    ROUTE_STATUS_ONE_MESSAGE = '82'
    ROUTE_STATUS_TWO_PK = 83
    ROUTE_STATUS_TWO_MESSAGE = '84'

    SERVICE_MAP_GROUP_ONE_PK = 101
    SERVICE_MAP_GROUP_ONE_ID = '102'

    SERVICE_PATTERN_ONE_PK = 91
    SERVICE_PATTERN_TWO_PK = 92

    STOP_ID_ALIAS_ONE = '101'
    STOP_ID_ALIAS_TWO = '102'

    EARLIEST_TERMINAL_TIME = '2018-11-02 10:00:30'
    MIDDLE_TERMINAL_TIME = '2018-11-02 11:00:20'
    LATEST_TERMINAL_TIME = '2018-11-02 12:00:10'

    LATEST_FEED_UPDATE_TIME = '2018-11-03 11:00:00'


class TestDataAccess(unittest.TestCase, TestDbConstants):

    @classmethod
    def setUpClass(cls):
        # TODO: make the sqllite DB in memory?
        toml_str = """
        [database]
        driver = 'sqlite'
        name = 'temp.db'
        """
        toml_str = """
        [database]
        driver = 'postgresql'
        name = 'transiter_test_db'
        """
        config.load_from_str(toml_str)
        database.ensure_db_connection()
        database.create_tables()

        test_db_dump_file_path = os.path.join(os.path.dirname(__file__), 'test_db_dump.sql')
        with open(test_db_dump_file_path) as f:
            query = text(f.read())

        parameters = {}
        for key, value in TestDbConstants.__dict__.items():
            if key[0] == '_':
                continue
            parameters[key.lower()] = value

        session = database.Session()
        session.execute(query, parameters)
        session.commit()

    @classmethod
    def _execute(cls, query, parameters):
        return database.Session().execute(query, parameters)

    def setUp(self):
        self.system_one = models.System()
        self.system_one.id = self.SYSTEM_ONE_ID
        self.system_one.package = self.SYSTEM_ONE_PACKAGE

        self.system_two = models.System()
        self.system_two.id = self.SYSTEM_TWO_ID
        self.system_two.package = self.SYSTEM_TWO_PACKAGE

        self.route_one = models.Route()
        self.route_one.id = self.ROUTE_ONE_ID
        self.route_one.system_id = self.SYSTEM_ONE_ID
        self.route_one.regular_service_pattern_pk = self.SERVICE_PATTERN_ONE_PK

        self.route_two = models.Route()
        self.route_two.id = self.ROUTE_TWO_ID
        self.route_two.system_id = self.SYSTEM_ONE_ID
        self.route_two.regular_service_pattern_pk = self.SERVICE_PATTERN_TWO_PK

        self.route_three = models.Route()
        self.route_three.id = self.ROUTE_THREE_ID
        self.route_three.system_id = self.SYSTEM_ONE_ID

        self.trip_one = models.Trip()
        self.trip_one.id = self.TRIP_ONE_ID
        self.trip_one.route_pk = self.ROUTE_ONE_PK
        self.trip_one.current_status = ''

        self.trip_two = models.Trip()
        self.trip_two.id = self.TRIP_TWO_ID
        self.trip_two.route_pk = self.ROUTE_ONE_PK
        self.trip_two.current_status = ''

        self.trip_three = models.Trip()
        self.trip_three.id = self.TRIP_THREE_ID
        self.trip_three.route_pk = self.ROUTE_ONE_PK
        self.trip_three.current_status = ''

        self.session = database.Session()

    def tearDown(self):
        self.session.rollback()

    #
    #   ROUTE DATA
    #

    def test__routedata__list_all_in_system(self):
        db_routes = routedam.list_all_in_system(self.SYSTEM_ONE_ID)

        self.assertListEqual(
            [self.route_one, self.route_two, self.route_three],
            list(db_routes))

    def test__routedata__get_in_system_by_id(self):
        db_route = routedam.get_in_system_by_id(
            self.SYSTEM_ONE_ID, self.ROUTE_ONE_ID)

        self.assertEqual(self.route_one, db_route)

    def test__routedata__get_id_to_pk_map_in_system(self):
        expected = {
            self.ROUTE_ONE_ID: self.ROUTE_ONE_PK,
            self.ROUTE_TWO_ID: self.ROUTE_TWO_PK,
            self.ROUTE_THREE_ID: self.ROUTE_THREE_PK,
            'unknown': None,
        }

        actual = routedam.get_id_to_pk_map_in_system(
            self.SYSTEM_ONE_ID, expected.keys())

        self.assertEqual(expected, actual)

    def test__routedata__list_terminus_data(self):
        data = routedam.calculate_frequency(self.ROUTE_ONE_PK)

        self.assertEqual(3596, int(data))

    def test__routedata__list_active_stop_ids(self):
        db_stop_ids = routedam.list_active_stop_ids(self.ROUTE_ONE_PK)

        self.assertListEqual(
            [self.STOP_ONE_ID, self.STOP_TWO_ID, self.STOP_THREE_ID, self.STOP_FOUR_ID],
            list(db_stop_ids))

    def test__routedata__list_active_stop_ids__no_stops(self):
        db_stop_ids = routedam.list_active_stop_ids(self.ROUTE_THREE_PK)

        self.assertEqual([], list(db_stop_ids))

    #
    #   STOP DATA
    #

    def test__stopdata__get_id_to_pk_map_in_system(self):
        expected = {
            self.STOP_ONE_ID: self.STOP_ONE_PK,
            self.STOP_TWO_ID: self.STOP_TWO_PK,
            'unknown': None,
        }

        actual = stopdam.get_id_to_pk_map_in_system(self.SYSTEM_ONE_ID, expected.keys())

        self.assertDictEqual(expected, actual)

    def test__stopdata__list_stop_time_updates_at_stops(self):
        data = list(stopdam.list_stop_time_updates_at_stops([self.STOP_FOUR_PK]))

        self.assertEqual(3, len(data))
        self.assertEqual(
            [self.TRIP_ONE_PK, self.TRIP_TWO_PK, self.TRIP_THREE_PK],
            [stop_event.trip_pk for stop_event in data]
        )

    #
    #   SERVICE PATTERN DATA
    #

    def test__servicepatterndata__get_default_trips_at_stops_map(self):
        actual = servicepatterndam.get_stop_pk_to_group_id_to_routes_map(
            [self.STOP_ONE_PK, self.STOP_TWO_PK, self.STOP_THREE_PK, self.STOP_FOUR_PK]
        )

        expected = {
            self.STOP_ONE_PK: {
                self.SERVICE_MAP_GROUP_ONE_ID: [self.route_one]
            },
            self.STOP_TWO_PK: {
                self.SERVICE_MAP_GROUP_ONE_ID: [self.route_one, self.route_two]
            },
            self.STOP_THREE_PK: {
                self.SERVICE_MAP_GROUP_ONE_ID: [self.route_two]
            },
            self.STOP_FOUR_PK: {}
        }

        self.maxDiff = None
        self.assertDictEqual(expected, actual)

    #
    #   TRIP DATA
    #

    def test__trip_dao__list_all_in_route(self):
        db_trips = tripdam.list_all_in_route(
            self.SYSTEM_ONE_ID, self.ROUTE_ONE_ID)

        self.assertEqual(
            [self.trip_one, self.trip_two, self.trip_three],
            list(db_trips))

    def test__trip_dao__list_all_in_route__no_trips(self):
        db_trips = tripdam.list_all_in_route(
            self.SYSTEM_ONE_ID, self.ROUTE_THREE_ID)

        self.assertEqual([], list(db_trips))

    def test__trip_dao__get_in_route_by_id(self):
        db_trip = tripdam.get_in_route_by_id(
            self.SYSTEM_ONE_ID, self.ROUTE_ONE_ID, self.TRIP_TWO_ID)

        self.assertEqual(self.trip_two, db_trip)

    def test__trip_dao__get_in_route_by_id__no_trip(self):
        db_trip = tripdam.get_in_route_by_id(
            self.SYSTEM_ONE_ID, self.ROUTE_THREE_ID, self.TRIP_ONE_ID)

        self.assertEqual(None, db_trip)

    def test__trip_dao__list_all_in_routes(self):
        expected = [self.trip_one, self.trip_two, self.trip_three]

        actual = list(tripdam.list_all_in_routes(
            self.SYSTEM_ONE_ID, [self.ROUTE_ONE_ID]
        ))

        self.assertListEqual(expected, actual)

    def test__trip_dao__list_all_in_routes__no_trips(self):
        expected = []

        actual = list(tripdam.list_all_in_routes(
            self.SYSTEM_ONE_ID, [self.ROUTE_TWO_ID, self.ROUTE_THREE_ID]
        ))

        self.assertListEqual(expected, actual)

    def test_get_trip_pk_to_future_stop_events_map(self):
        trip_pks_to_stop_pks = {
            self.TRIP_ONE_PK: [self.STOP_ONE_PK, self.STOP_TWO_PK, self.STOP_THREE_PK, self.STOP_FOUR_PK],
            self.TRIP_TWO_PK: [self.STOP_ONE_PK, self.STOP_TWO_PK, self.STOP_FOUR_PK],
            self.TRIP_THREE_PK: [self.STOP_ONE_PK, self.STOP_FOUR_PK],
        }

        data = tripdam.get_trip_pk_to_future_stop_events_map(
            trip_pks_to_stop_pks.keys()
        )

        for trip_pk, stop_events in data.items():
            stop_pks = [stop_event.stop_pk for stop_event in stop_events]
            self.assertEqual(trip_pks_to_stop_pks[trip_pk], stop_pks)

    #
    #   SYSTEM DATA
    #

    def test__system_dao__count_stops_in_system(self):
        count = systemdam.count_stops_in_system(self.SYSTEM_ONE_ID)

        self.assertEqual(5, count)

    def test__system_dao__count_routes_in_system(self):
        count = systemdam.count_routes_in_system(self.SYSTEM_ONE_ID)

        self.assertEqual(3, count)

    def test__system_dao__count_feeds_in_system(self):
        count = systemdam.count_feeds_in_system(self.SYSTEM_ONE_ID)

        self.assertEqual(2, count)

    def test__base_entity_dao__list_all(self):
        db_system = systemdam.list_all()

        self.assertListEqual(
            [self.system_one, self.system_two],
            list(db_system))

    def test__base_entity_dao__get_by_id(self):
        db_system = systemdam.get_by_id(self.SYSTEM_ONE_ID)

        self.assertEqual(self.system_one, db_system)

    def test__base_entity_dao__get_by_id__no_result(self):
        db_system = systemdam.get_by_id(self.SYSTEM_THREE_ID)

        self.assertEqual(None, db_system)

    def test__base_entity_dao__create(self):
        db_system = systemdam.create()
        db_system.id = self.SYSTEM_THREE_ID
        db_system.name = self.SYSTEM_THREE_NAME
        db_system.package = self.SYSTEM_THREE_PACKAGE
        self.session.flush()

        query = "SELECT id, name FROM system WHERE id=:system_id"
        result = self._execute(query, {'system_id': self.SYSTEM_THREE_ID})
        row = result.fetchone()

        self.assertEqual(row[0], self.SYSTEM_THREE_ID)
        self.assertEqual(row[1], self.SYSTEM_THREE_NAME)

    def test__base_entity_dao__delete(self):
        response = systemdam.delete_by_id(self.SYSTEM_TWO_ID)
        self.session.flush()

        query = "SELECT id, name FROM system WHERE id=:system_id"
        result = self._execute(query, {'system_id': self.SYSTEM_TWO_ID})
        row = result.fetchone()

        self.assertEqual(row, None)
        self.assertEqual(response, True)

    def test__base_entity_dao__delete__none_to_delete(self):
        response = systemdam.delete_by_id(self.SYSTEM_THREE_ID)

        self.assertEqual(response, False)

    #
    #   FEED DATA
    #

    def test__feed_dao__get_last_successful_update(self):
        db_feed_update = feeddam.get_last_successful_update(self.FEED_ONE_PK)

        self._compare_datetime_to_str(
            db_feed_update.last_action_time,
            self.LATEST_FEED_UPDATE_TIME)
        db_feed_update.last_action_time = None

        feed_update = models.FeedUpdate(None)
        feed_update.feed_pk = self.FEED_ONE_PK
        feed_update.status = 'SUCCESS'

        self.assertEqual(feed_update, db_feed_update)

    def test__feed_dao__list_updates_in_feed(self):
        feed = feeddam.get_in_system_by_id(self.SYSTEM_ONE_ID, self.FEED_ONE_ID)
        data = list(feeddam.list_updates_in_feed(feed))
        self.assertEqual(3, len(data))
        self.assertEqual(
            ['SUCCESS', 'SUCCESS', 'FAILURE'],
            [feed_update.status for feed_update in data]
        )

    def _compare_datetime_to_str(self, dt, st):
        self.assertEqual(str(dt)[:-6], st)

    @classmethod
    def tearDownClass(cls):
        pass
        # database.close_db_connection()
        # database.drop_database()
