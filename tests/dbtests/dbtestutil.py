import unittest
from transiter.data import dbconnection
from transiter import config

from . import testdata

_db_setup = False


def ensure_db_setup():
    global _db_setup
    if _db_setup:
        return
    _db_setup = True
    toml_str = """
    [database]
    driver = 'postgresql'
    name = 'transiter_test_db'
    """
    config.load_from_str(toml_str)
    dbconnection.ensure_db_connection()
    dbconnection.rebuild_db()

    session = dbconnection.Session()
    session.add(testdata.system_one)
    session.add(testdata.system_two)
    session.commit()


class TestCase(unittest.TestCase):
    def setUp(self):
        ensure_db_setup()
        self.session = dbconnection.get_session()

    def tearDown(self):
        self.session.rollback()
