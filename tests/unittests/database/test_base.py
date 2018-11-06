import unittest
from transiter.database.models import base
from sqlalchemy import Column, String, Integer


class TestBasicModel(unittest.TestCase):

    def test_short_repr(self):

        class TestModel(base._BasicModel):

            _short_repr_list = ['A']
            _short_repr_dict = {'B': 'C'}

        test_model = TestModel()
        test_model.A = '1'
        test_model.C = '2'

        expected_short_repr = {
            'B': '2',
            'A': '1'
        }

        actual_short_repr = test_model.short_repr()

        self.assertEqual(expected_short_repr, actual_short_repr)

    def test_long_repr(self):

        class TestModel(base._BasicModel):

            _long_repr_list = ['A']
            _long_repr_dict = {'B': 'C'}

        test_model = TestModel()
        test_model.A = '1'
        test_model.C = '2'

        expected_long_repr = {
            'B': '2',
            'A': '1'
        }

        actual_long_repr = test_model.long_repr()

        self.assertEqual(expected_long_repr, actual_long_repr)

    def test_not_implemented(self):

        class TestModel(base._BasicModel):
            pass

        test_model = TestModel()

        self.assertRaises(NotImplementedError, test_model.short_repr)

    def test_equality(self):

        model_one = FakeDbModel()
        model_one.column = 'A'
        model_two = FakeDbModel()
        model_two.column = 'A'

        self.assertEqual(model_one, model_two)

    def test_no_equality(self):

        model_one = FakeDbModel()
        model_one.column = 'A'
        model_two = FakeDbModel()
        model_two.column = 'B'

        self.assertNotEqual(model_one, model_two)


class FakeDbModel(base.Base):
    __tablename__ = 'fake_db_model'
    id = Column(Integer, primary_key=True)
    column = Column(String)
