from . import testutil

import unittest
from unittest import mock

from transiter import config, exceptions


class TestConfig(testutil.TestCase(config), unittest.TestCase):
    NEW_DATABASE_PORT = "1232"
    NEW_TASK_SERVER_PORT = "10001"

    def test_load_from_str(self):
        """[Config] Load config from string"""
        new_config = """
        [database]
        port = '{}'
        something_else = 'blah'
        
        [taskserver]
        port = '{}'
        """.format(
            self.NEW_DATABASE_PORT, self.NEW_TASK_SERVER_PORT
        )

        config.load_from_str(new_config)

        self.assertEqual(self.NEW_DATABASE_PORT, config.DatabaseConfig.PORT)
        self.assertEqual(self.NEW_TASK_SERVER_PORT, config.TaskServerConfig.PORT)


class TestLoadConfig(testutil.TestCase(config), unittest.TestCase):
    CUSTOM_FILE = "special-config.toml"
    TOML_STRING = "BlahBlah"

    def setUp(self):
        self.os = self.mockImportedModule(config.os)
        self.os.environ = {}
        patcher = mock.patch.object(config, "open")
        self.open = patcher.start()
        self.addCleanup(patcher.stop)
        self.load_from_str = self.mockModuleAttribute("load_from_str")

        self.file_handle = mock.MagicMock()
        self.file_handle.read.return_value = self.TOML_STRING

    def test_load__from_custom_file__file_found(self):
        """[Config] Test load from custom file"""
        self.open.return_value = self._FakeContextManager(self.file_handle)

        config.load(self.CUSTOM_FILE)

        self.open.assert_called_once_with(self.CUSTOM_FILE, "r")
        self.load_from_str.assert_called_once_with(self.TOML_STRING)

    def test_load__from_custom_file__file_not_found(self):
        """[Config] Test load from custom file - file not found"""
        self.open.side_effect = FileNotFoundError

        self.assertRaises(
            exceptions.ConfigFileNotFoundError, lambda: config.load(self.CUSTOM_FILE)
        )

        self.open.assert_called_once_with(self.CUSTOM_FILE, "r")

    def test_load__from_env_variable__file_found(self):
        """[Config] Test load from environment variable"""
        self.open.return_value = self._FakeContextManager(self.file_handle)
        self.os.environ = {"TRANSITER_CONFIG": self.CUSTOM_FILE}

        config.load()

        self.open.assert_called_once_with(self.CUSTOM_FILE, "r")
        self.load_from_str.assert_called_once_with(self.TOML_STRING)

    def test_load__from_env_variable__file_not_found(self):
        """[Config] Test load from environment variable - file not found"""
        self.open.side_effect = FileNotFoundError
        self.os.environ = {"TRANSITER_CONFIG": self.CUSTOM_FILE}

        self.assertRaises(exceptions.ConfigFileNotFoundError, lambda: config.load())

        self.open.assert_called_once_with(self.CUSTOM_FILE, "r")

    def test_load__from_default_file__file_found(self):
        """[Config] Test load from default file"""
        self.open.return_value = self._FakeContextManager(self.file_handle)

        config.load()

        self.open.assert_called_once_with(config.DEFAULT_FILE_PATH, "r")
        self.load_from_str.assert_called_once_with(self.TOML_STRING)

    def test_load__from_default_file__file_not_found(self):
        """[Config] Test load from default file - file not found"""
        self.open.side_effect = FileNotFoundError

        config.load()

        self.open.assert_called_once_with(config.DEFAULT_FILE_PATH, "r")
        self.load_from_str.assert_not_called()
