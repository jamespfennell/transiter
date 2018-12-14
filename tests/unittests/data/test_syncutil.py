import unittest
from unittest import mock

from transiter.data import syncutil


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

    def test_copy_pks(self):

        new_model = self.MockDbModel('1')
        updated_model_new = self.MockDbModel('2')
        updated_model_old = self.MockDbModel('2')
        updated_model_old.pk = 2
        old_model = self.MockDbModel('3')
        old_model.pk = 3

        (old_models, updated_model_tuples, new_models) = syncutil.copy_pks(
            [updated_model_old, old_model], [new_model, updated_model_new],
            ('id', )
        )

        self.assertEqual([old_model], old_models)
        self.assertEqual([new_model], new_models)
        self.assertEqual([(updated_model_old, updated_model_new)], updated_model_tuples)

