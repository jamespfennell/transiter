import unittest
from transiter.data import database
from transiter import config

from . import testdata

_db_setup = False


def ensure_db_setup():
    global _db_setup
    if _db_setup:
        return
    _db_setup = True
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
    database.rebuild_db()

    session = database.Session()
    session.add(testdata.system_one)
    session.add(testdata.system_two)
    session.commit()


class TestCase(unittest.TestCase):
    def setUp(self):
        ensure_db_setup()
        self.session = database.get_session()

    def tearDown(self):
        self.session.rollback()
