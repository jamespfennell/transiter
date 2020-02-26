import enum
import unittest

import strictyaml
from strictyaml import Map
from strictyaml.exceptions import YAMLValidationError, YAMLSerializationError

from transiter import models, exceptions
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


class TestReadConfig(unittest.TestCase):
    SYSTEM_NAME = "Test System"
    FEED_ID = "GTFS"
    URL = "https://transiter.io"
    SETTING_VALUE = "value"

    def test_base_case(self):
        """[System config reader] Base case"""

        config = f"""
        {systemconfigreader.NAME}: "{self.SYSTEM_NAME}"

        {systemconfigreader.FEEDS}:
          {self.FEED_ID}:
            http:
              url: {self.URL}
            parser:
              built_in: GTFS_STATIC
        """

        expected = {
            systemconfigreader.NAME: self.SYSTEM_NAME,
            "requirements": {"packages": [], "settings": []},
            "feeds": {
                self.FEED_ID: {
                    "http": {"url": self.URL, "headers": {}},
                    "parser": {"built_in": models.Feed.BuiltInParser.GTFS_STATIC},
                    "auto_update": {"enabled": False, "period": -1},
                    "required_for_install": False,
                }
            },
        }

        actual = systemconfigreader.read(config)
        del actual["service_maps"]

        self.maxDiff = None
        self.assertDictEqual(expected, actual)

    def test_yaml_schema_error(self):
        """[System config reader] Yaml schema error"""

        config = """
        random_key:
          and_again: 2
        """

        self.assertRaises(
            exceptions.InvalidSystemConfigFile, lambda: systemconfigreader.read(config)
        )

    def test_yaml_parser_error(self):
        """[System config reader] Yaml parser error"""

        config = """
        random_key:
        <HTML TAG>
            Ramon ind
          and_again: 2
        """

        self.assertRaises(
            exceptions.InvalidSystemConfigFile, lambda: systemconfigreader.read(config)
        )
        pass

    def test_missing_settings(self):
        """[System config reader] Missing setting"""

        config = f"""
        {systemconfigreader.NAME}: "{self.SYSTEM_NAME}"

        {systemconfigreader.REQUIREMENTS}:
          {systemconfigreader.SETTINGS}:
            -setting_name

        {systemconfigreader.FEEDS}:
          {self.FEED_ID}:
            http:
              url: "{{setting_name}}"
            parser:
              built_in: GTFS_STATIC
        """

        self.assertRaises(
            exceptions.InvalidSystemConfigFile, lambda: systemconfigreader.read(config)
        )

    def test_substitute_settings(self):
        """[System config reader] Substitute setting"""

        config = f"""
        {systemconfigreader.NAME}: "{self.SYSTEM_NAME}"

        {systemconfigreader.REQUIREMENTS}:
          {systemconfigreader.SETTINGS}:
            - setting_name

        {systemconfigreader.FEEDS}:
          {self.FEED_ID}:
            http:
              url: "{{setting_name}}"
            parser:
              built_in: GTFS_STATIC
        """

        self.assertEqual(
            self.SETTING_VALUE,
            systemconfigreader.read(config, {"setting_name": self.SETTING_VALUE})[
                systemconfigreader.FEEDS
            ][self.FEED_ID][systemconfigreader.HTTP][systemconfigreader.URL],
        )
