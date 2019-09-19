import enum
import unittest

import strictyaml
from strictyaml import Map
from strictyaml.exceptions import YAMLValidationError, YAMLSerializationError

from transiter.services import systemconfigreader


class TestHumanReadableTimePeriod(unittest.TestCase):

    schema = Map({"test": systemconfigreader.HumanReadableTimePeriod()})

    def test_read_valid(self):
        """[System config reader | HumanReadableTimePeriod] Read valid"""
        result = strictyaml.load("test: 5 minutes", self.schema)

        self.assertDictEqual({"test": 300}, dict(result))

    def test_read_invalid(self):
        """[System config reader | HumanReadableTimePeriod] Read invalid"""
        self.assertRaises(
            YAMLValidationError, lambda: strictyaml.load("test: THIRD", self.schema)
        )

    def test_write(self):
        """[System config reader | HumanReadableTimePeriod] Read write"""
        yaml = strictyaml.as_document({"test": 7}, schema=self.schema).as_yaml()

        self.assertEqual("test: 7 seconds", yaml.strip())


class TestPyEnum(unittest.TestCase):
    class MyEnum(enum.Enum):
        FIRST = 1
        SECOND = 2

    schema = Map({"test": systemconfigreader.PyEnum(MyEnum)})

    def test_read_valid(self):
        """[System config reader | PyEnum] Read valid"""
        result = strictyaml.load("test: FIRST", self.schema)

        self.assertDictEqual({"test": self.MyEnum.FIRST}, dict(result.data))

    def test_read_invalid(self):
        """[System config reader | PyEnum] Read invalid"""
        self.assertRaises(
            YAMLValidationError, lambda: strictyaml.load("test: THIRD", self.schema)
        )

    def test_write_valid(self):
        """[System config reader | PyEnum] Write valid"""
        yaml = strictyaml.as_document(
            {"test": self.MyEnum.FIRST}, schema=self.schema
        ).as_yaml()

        self.assertEqual("test: FIRST", yaml.strip())

    def test_write_invalid(self):
        """[System config reader | PyEnum] Write invalid"""
        self.assertRaises(
            YAMLSerializationError,
            lambda: strictyaml.as_document(
                {"test": "FIRST"}, schema=self.schema
            ).as_yaml(),
        )

    def test_instantiate_without_enum(self):
        """[System config reader | PyEnum] Instantiate without enum"""

        class DummyClass:
            pass

        self.assertRaises(AssertionError, lambda: systemconfigreader.PyEnum(DummyClass))
