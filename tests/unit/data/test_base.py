import unittest
from transiter.models import base
from sqlalchemy import Column, String, Integer


class TestBasicModel(unittest.TestCase):
    def _test_short_repr(self):
        class TestModel(base.Base):
            __tablename__ = "blak"
            pk = Column(Integer, primary_key=True)
            id = Column(String)
            name = Column(String)

            _short_repr_list = [id]
            _short_repr_dict = {"full_name": name}

        test_model = TestModel()
        test_model.id = "L"
        test_model.name = "James"

        expected_short_repr = {"id": "L", "full_name": "James"}

        actual_short_repr = test_model.short_repr()

        self.assertEqual(expected_short_repr, actual_short_repr)

    def test_long_repr(self):
        class TestModel(base.Base):
            __tablename__ = "blak2"
            pk = Column(Integer, primary_key=True)
            id = Column(String)
            name = Column(String)

            _long_repr_list = [id]
            _long_repr_dict = {"full_name": name}

        test_model = TestModel()
        test_model.id = "L"
        test_model.name = "James"

        expected_long_repr = {"id": "L", "full_name": "James"}

        actual_long_repr = test_model.long_repr()

        self.assertEqual(expected_long_repr, actual_long_repr)

    # TODO: this test is failing on Travis for some SQL Alchemy reason. Re-enable
    # when possible.
    def _test_not_implemented(self):
        class TestModel(base.Base):
            __tablename__ = "blak3"
            pk = Column(Integer, primary_key=True)
            id = Column(String)
            name = Column(String)

        test_model = TestModel()
        test_model.id = "L"
        test_model.name = "James"

        self.assertRaises(NotImplementedError, test_model.short_repr)

    def test_equality(self):

        model_one = FakeDbModel()
        model_one.column = "A"
        model_two = FakeDbModel()
        model_two.column = "A"

        self.assertEqual(model_one, model_two)

    def test_no_equality(self):

        model_one = FakeDbModel()
        model_one.column = "A"
        model_two = FakeDbModel()
        model_two.column = "B"

        self.assertNotEqual(model_one, model_two)


class FakeDbModel(base.Base):
    __tablename__ = "fake_db_model"
    id = Column(Integer, primary_key=True)
    column = Column(String)
