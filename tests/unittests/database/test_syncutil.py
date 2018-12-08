import unittest
from unittest import mock

from transiter.database import syncutil
from transiter import models


class TestSync(unittest.TestCase):

    ID_ONE = 4
    ID_TWO = 5
    ID_THREE = 6
    OLD_VALUE_ONE = "1"
    OLD_VALUE_TWO = "2"
    NEW_VALUE_TWO = "3"
    NEW_VALUE_THREE = "4"

    class MockDbModel:

        def __init__(self, id=None, value=None):
            self.id = id
            self.key = value

        def __eq__(self, other):
            return self.__dict__ == other.__dict__

        def __hash__(self):
            return hash(str(self))

        def __str__(self):
            return str(self.__dict__)

        def __repr__(self):
            return str(self)

    @mock.patch('transiter.database.syncutil.connection')
    def test_sync(self, connection):
        """[Database sync] Sync data"""

        def add_function(entity):
            self._new_entities.add(entity)

        def delete_function(session, entity):
            self._deleted_entities.add(entity)

        session = mock.MagicMock()
        connection.get_session.return_value = session
        session.add.side_effect = add_function

        self._new_entities = set()
        self._deleted_entities = set()

        old_one = self.MockDbModel(self.ID_ONE, self.OLD_VALUE_ONE)
        old_two = self.MockDbModel(self.ID_TWO, self.OLD_VALUE_TWO)
        new_two = self.MockDbModel(self.ID_TWO, self.NEW_VALUE_TWO)
        new_three = self.MockDbModel(self.ID_THREE, self.NEW_VALUE_THREE)
        db_entities = [old_one, old_two]
        expected_new_db_entities = [new_two, new_three]
        new_entities = [
            {
                'id': self.ID_TWO,
                'key': self.NEW_VALUE_TWO
            },
            None,
            {
                'id': self.ID_THREE,
                'key': self.NEW_VALUE_THREE
            }
        ]

        actual_new_db_entities = syncutil.sync(
            self.MockDbModel, db_entities, new_entities, ['id'], delete_function)

        self.assertListEqual(actual_new_db_entities, expected_new_db_entities)
        self.assertSetEqual(self._deleted_entities, {old_one})
        # NOTE: Unittest's assertSetEqual uses set.difference() which does
        # not use the obj.__eq__ method, so sets containing objects with the
        # the same data fail the assertion
        self.assertListEqual(list(self._new_entities), [new_three])

    def _session_add(self, entity):
        self._new_entities.add(entity)

    def test_delete_from_db(self):
        session = mock.MagicMock()
        entity = mock.MagicMock()

        syncutil.delete_from_db(session, entity)

        session.delete.assert_called_once_with(entity)

