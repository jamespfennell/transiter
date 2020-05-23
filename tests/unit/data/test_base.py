import unittest

from sqlalchemy import Column, String, Integer

from transiter.db.models import base


class TestBasicModel(unittest.TestCase):
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
