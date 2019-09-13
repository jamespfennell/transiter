import unittest

from transiter.data import dbconnection
from . import testdata

_db_setup = False


def ensure_db_setup():
    global _db_setup
    if _db_setup:
        return
    _db_setup = True
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
