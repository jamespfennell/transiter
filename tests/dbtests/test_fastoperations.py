from transiter import models
from transiter.data import fastoperations
from transiter.data.dams import systemdam
from . import dbtestutil, testdata


class TestFastOperations(dbtestutil.TestCase):

    NEW_SYSTEM_1_DICT = {"id": "A", "name": "B"}
    NEW_SYSTEM_2_DICT = {"id": "C", "name": "D"}
    NEW_SYSTEM_3_DICT = {"id": "E", "name": "F"}

    def setUp(self):
        super().setUp()
        self.new_system_1 = models.System(**self.NEW_SYSTEM_1_DICT)
        self.new_system_2 = models.System(**self.NEW_SYSTEM_2_DICT)
        self.new_system_3 = models.System(**self.NEW_SYSTEM_3_DICT)

    def test_fast_insert(self):
        """[Fast operations] Fast insert"""
        fast_inserter = fastoperations.FastInserter(models.System, batch_size=10)

        fast_inserter.add(self.NEW_SYSTEM_1_DICT)
        fast_inserter.flush()
        self.session.flush()

        self.assertEqual(
            [testdata.system_one, testdata.system_two, self.new_system_1],
            systemdam.list_all(),
        )

    def test_fast_insert_batching(self):
        """[Fast operations] Fast insert"""
        fast_inserter = fastoperations.FastInserter(models.System, batch_size=2)

        fast_inserter.add(self.NEW_SYSTEM_1_DICT)
        fast_inserter.add(self.NEW_SYSTEM_2_DICT)
        fast_inserter.add(self.NEW_SYSTEM_3_DICT)
        self.session.flush()

        self.assertEqual(
            [
                testdata.system_one,
                testdata.system_two,
                self.new_system_1,
                self.new_system_2,
            ],
            systemdam.list_all(),
        )
