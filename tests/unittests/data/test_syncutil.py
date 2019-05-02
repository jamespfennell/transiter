import unittest

from transiter.data import syncutil


class TestSync(unittest.TestCase):
    class MockDbModel:
        def __init__(self, id_=None, pk=None):
            self.pk = pk
            self.id = id_

        def __eq__(self, other):
            return self.__dict__ == other.__dict__

    def test_copy_pks(self):
        """[Sync util] Copy PKs"""
        new_model = self.MockDbModel("1")
        updated_model_new = self.MockDbModel("2")
        updated_model_old = self.MockDbModel("2", 2)
        old_model = self.MockDbModel("3", 3)

        (old_models, updated_model_tuples, new_models) = syncutil.copy_pks(
            [updated_model_old, old_model], [new_model, updated_model_new], ("id",)
        )

        self.assertEqual([old_model], old_models)
        self.assertEqual([new_model], new_models)
        self.assertEqual([(updated_model_old, updated_model_new)], updated_model_tuples)
