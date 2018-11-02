import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from transiter.database import creator
from transiter.database import connection
from transiter.database.daos import route_dao
from transiter.database import models


from transiter.services import systemservice

class TestDaos(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        test_db_name = 'transiter_test_db'
        creator.create_database(test_db_name)

        connection.engine = create_engine("postgres://postgres@/{}".format(test_db_name))
        connection.session_factory = sessionmaker(bind=connection.engine)
        connection.Session = scoped_session(connection.session_factory)

        creator.create_tables()

        query = """
        INSERT INTO systems (system_id) VALUES ('system_one_id');
        
        INSERT INTO routes (route_id, system_id) VALUES ('route_one_id', 'system_one_id');
        """
        connection.engine.execute(query)
        # systemservice.install('nycsubway')


    def setUp(self):
        self.route_one = models.Route()
        self.route_one.route_id = 'route_one_id'
        self.route_one.system_id = 'system_one_id'

    def test__system_child_entity_dao__get_in_system_by_id(self):

        db_route = route_dao.get_in_system_by_id('system_one_id', 'route_one_id')
        self.assertEqual(self.route_one, db_route)



    @classmethod
    def tearDownClass(cls):
        pass
        #creator.drop_db()
