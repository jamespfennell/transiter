from transiter.data import dbconnection
import unittest


class TestDBConnection(unittest.TestCase):
    def test_outside_unit_of_work_error__before(self):
        """[DB Connection] Outside unit of work - before"""

        self.assertRaises(
            dbconnection.OutsideUnitOfWorkError, lambda: dbconnection.get_session()
        )

    def test_outside_unit_of_work_error__after(self):
        """[DB Connection] Outside unit of work - after"""

        @dbconnection.unit_of_work
        def uow():
            return 1 + 1

        uow()

        self.assertRaises(
            dbconnection.OutsideUnitOfWorkError, lambda: dbconnection.get_session()
        )

    def test_nested_unit_of_work_error(self):
        """[DB Connection] Nest unit of work"""

        @dbconnection.unit_of_work
        def uow_1():
            return 1 + 1

        @dbconnection.unit_of_work
        def uow_2():
            return uow_1()

        self.assertRaises(dbconnection.NestedUnitOfWorkError, uow_2)
