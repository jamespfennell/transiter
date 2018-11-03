import unittest
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from transiter.database import creator
from transiter.database import connection
from transiter.database.daos import route_dao
from transiter.database.daos import system_dao, trip_dao
from transiter.database import models
import os


class TestDbConstants:

    SYSTEM_ONE_ID = '1'
    SYSTEM_TWO_ID = '2'
    SYSTEM_THREE_ID = '3'
    SYSTEM_THREE_NAME = '4'

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

    EARLIEST_TERMINAL_TIME = '2018-11-02 10:00:30'
    MIDDLE_TERMINAL_TIME = '2018-11-02 11:00:20'
    LATEST_TERMINAL_TIME = '2018-11-02 12:00:10'


class TestDaos(unittest.TestCase, TestDbConstants):

    @classmethod
    def setUpClass(cls):
        test_db_name = 'transiter_test_db'
        creator.create_database(test_db_name)

        connection.engine = create_engine("postgres://postgres@/{}".format(test_db_name))
        connection.session_factory = sessionmaker(bind=connection.engine)
        connection.Session = scoped_session(connection.session_factory)

        creator.create_tables()

        test_db_dump_file_path = os.path.join(os.path.dirname(__file__), 'test_db_dump.sql')
        with open(test_db_dump_file_path) as f:
            query = text(f.read())
            print(query)

        parameters = {}
        for key, value in TestDbConstants.__dict__.items():
            parameters[key.lower()] = value
        cls._execute(query, parameters)
        connection.Session().commit()
        connection.Session.remove()

    @classmethod
    def _execute(self, query, parameters):
        return connection.Session().execute(query, parameters)

    def setUp(self):
        self.system_one = models.System()
        self.system_one.system_id = self.SYSTEM_ONE_ID

        self.system_two = models.System()
        self.system_two.system_id = self.SYSTEM_TWO_ID

        self.route_one = models.Route()
        self.route_one.route_id = self.ROUTE_ONE_ID
        self.route_one.system_id = self.SYSTEM_ONE_ID

        self.route_two = models.Route()
        self.route_two.route_id = self.ROUTE_TWO_ID
        self.route_two.system_id = self.SYSTEM_ONE_ID

        self.route_three = models.Route()
        self.route_three.route_id = self.ROUTE_THREE_ID
        self.route_three.system_id = self.SYSTEM_ONE_ID

        self.trip_one = models.Trip()
        self.trip_one.trip_id = self.TRIP_ONE_ID
        self.trip_one.route_pri_key = self.ROUTE_ONE_PK
        self.trip_one.current_status = ''

        self.trip_two = models.Trip()
        self.trip_two.trip_id = self.TRIP_TWO_ID
        self.trip_two.route_pri_key = self.ROUTE_ONE_PK
        self.trip_two.current_status = ''

        self.trip_three = models.Trip()
        self.trip_three.trip_id = self.TRIP_THREE_ID
        self.trip_three.route_pri_key = self.ROUTE_ONE_PK
        self.trip_three.current_status = ''

        self.session = connection.Session()

    def tearDown(self):
        self.session.rollback()

    def test__base_entity_dao__list_all(self):
        db_system = system_dao.list_all()

        self.assertListEqual(
            [self.system_one, self.system_two],
            list(db_system))

    def test__base_entity_dao__get_by_id(self):
        db_system = system_dao.get_by_id(self.SYSTEM_ONE_ID)

        self.assertEqual(self.system_one, db_system)

    def test__base_entity_dao__get_by_id__no_result(self):
        db_system = system_dao.get_by_id(self.SYSTEM_THREE_ID)

        self.assertEqual(None, db_system)

    def test__base_entity_dao__create(self):
        db_system = system_dao.create()
        db_system.system_id = self.SYSTEM_THREE_ID
        db_system.name = self.SYSTEM_THREE_NAME
        self.session.flush()

        query = "SELECT system_id, name FROM systems WHERE system_id=:system_id"
        result = self._execute(query, {'system_id': self.SYSTEM_THREE_ID})
        row = result.fetchone()

        self.assertEqual(row[0], self.SYSTEM_THREE_ID)
        self.assertEqual(row[1], self.SYSTEM_THREE_NAME)

    def test__base_entity_dao__delete(self):
        response = system_dao.delete_by_id(self.SYSTEM_ONE_ID)
        self.session.flush()

        query = "SELECT system_id, name FROM systems WHERE system_id=:system_id"
        result = self._execute(query, {'system_id': self.SYSTEM_ONE_ID})
        row = result.fetchone()

        self.assertEqual(row, None)
        self.assertEqual(response, True)

    def test__base_entity_dao__delete__none_to_delete(self):
        response = system_dao.delete_by_id(self.SYSTEM_THREE_ID)

        self.assertEqual(response, False)

    def test__system_child_entity_dao__get_in_system_by_id(self):
        db_route = route_dao.get_in_system_by_id(
            self.SYSTEM_ONE_ID, self.ROUTE_ONE_ID)

        self.assertEqual(self.route_one, db_route)

    def test__system_child_entity_dao__list_all_in_system(self):
        db_routes = route_dao.list_all_in_system(self.SYSTEM_ONE_ID)

        self.assertListEqual(
            [self.route_one, self.route_two, self.route_three],
            list(db_routes))

    def test__trip_dao__list_all_in_route(self):
        db_trips = trip_dao.list_all_in_route(
            self.SYSTEM_ONE_ID, self.ROUTE_ONE_ID)

        self.assertEqual(
            [self.trip_one, self.trip_two, self.trip_three],
            list(db_trips))

    def test__trip_dao__list_all_in_route__no_trips(self):
        db_trips = trip_dao.list_all_in_route(
            self.SYSTEM_ONE_ID, self.ROUTE_THREE_ID)

        self.assertEqual([], list(db_trips))

    def test__trip_dao__get_in_route_by_id(self):
        db_trip = trip_dao.get_in_route_by_id(
            self.SYSTEM_ONE_ID, self.ROUTE_ONE_ID, self.TRIP_TWO_ID)

        self.assertEqual(self.trip_two, db_trip)

    def test__trip_dao__get_in_route_by_id__no_trip(self):
        db_trip = trip_dao.get_in_route_by_id(
            self.SYSTEM_ONE_ID, self.ROUTE_THREE_ID, self.TRIP_ONE_ID)

        self.assertEqual(None, db_trip)

    def test__route_dao__get_active_stop_ids(self):
        db_stop_ids = route_dao.get_active_stop_ids(self.ROUTE_ONE_PK)

        self.assertListEqual(
            [self.STOP_ONE_ID, self.STOP_TWO_ID, self.STOP_THREE_ID, self.STOP_FOUR_ID],
            list(db_stop_ids))

    def test__route_dao__get_active_stop_ids__no_stops(self):
        db_stop_ids = route_dao.get_active_stop_ids(self.ROUTE_THREE_PK)

        self.assertEqual([], list(db_stop_ids))

    def test__route_dao__get_terminus_data(self):
        data = list(route_dao.get_terminus_data(self.ROUTE_ONE_PK))

        self.assertEqual(len(data), 1)

        row = data[0]
        self.assertEqual(str(row[0])[:-6], self.EARLIEST_TERMINAL_TIME)
        self.assertEqual(str(row[1])[:-6], self.LATEST_TERMINAL_TIME)
        self.assertEqual(row[2], 3)
        self.assertEqual(row[3], self.STOP_FOUR_PK)

    @classmethod
    def tearDownClass(cls):
        pass
        #creator.drop_db()
