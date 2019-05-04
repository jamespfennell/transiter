import unittest
from unittest import mock
from click.testing import CliRunner

from transiter import clt, config, exceptions
from . import testutil


class TestClr(testutil.TestCase(clt), unittest.TestCase):
    CONFIG_FILE = "my-file.toml"
    TOML_CONFIG = "blah"

    def setUp(self):
        self.config = self.mockImportedModule(clt.config)
        self.flaskapp = self.mockImportedModule(clt.flaskapp)
        self.taskserver = self.mockImportedModule(clt.taskserver)
        self.database = self.mockImportedModule(clt.dbconnection)
        self.runner = CliRunner()
        patcher = mock.patch.object(clt, "open")
        self.open = patcher.start()
        self.addCleanup(patcher.stop)
        self.file_handle = mock.MagicMock()

        self.database_config = mock.MagicMock()
        self.config.DefaultDatabaseConfig = self.database_config
        self.task_server_config = mock.MagicMock()
        self.config.DefaultTaskServerConfig = self.task_server_config
        self.config.generate.return_value = self.TOML_CONFIG

    def test_launch_taskserver(self):
        """[CLT] Launch Task Server"""
        self._run(["launch", "task-server"])

        self.taskserver.launch.assert_called_once_with(False)

    def test_launch_taskserver_different_config(self):
        """[CLT] Launch Task Server with different config"""
        self._run(["-c", self.CONFIG_FILE, "launch", "task-server"])

        self.taskserver.launch.assert_called_once_with(False)
        self.config.load.assert_called_once_with(self.CONFIG_FILE)

    def test_launch_taskserver_different_bad_config(self):
        """[CLT] Launch Task Server with unknown config file"""
        self.config.load.side_effect = exceptions.ConfigFileNotFoundError

        self._run(["-c", self.CONFIG_FILE, "launch", "task-server"])

        self.taskserver.launch.assert_not_called()
        self.config.load.assert_called_once_with(self.CONFIG_FILE)

    def test_launch_flask_app(self):
        """[CLT] Launch Flask app"""
        self._run(["launch", "http-debug-server"])

        self.flaskapp.launch.assert_called_once_with(False)

    def test_launch_flask_app__forced(self):
        """[CLT] Launch Flask app - forced"""
        self._run(["launch", "-f", "http-debug-server"])

        self.flaskapp.launch.assert_called_once_with(True)

    def test_generate_config__default_case(self):
        """[CLT] Generate config, write to file"""
        self.open.return_value = self._FakeContextManager(self.file_handle)

        self._run(["generate-config", "-o", self.CONFIG_FILE])

        self.open.assert_called_once_with(self.CONFIG_FILE, "x")
        self.config.generate.assert_called_once_with(
            database_config=self.database_config,
            task_server_config=self.task_server_config,
        )
        self.file_handle.write.assert_called_once_with(self.TOML_CONFIG)

    def test_generate_config__write_failure(self):
        """[CLT] Generate config - file exists and write fails"""
        self.open.side_effect = FileExistsError

        self._run(["generate-config", "-o", self.CONFIG_FILE])

        self.open.assert_called_once_with(self.CONFIG_FILE, "x")
        self.config.generate.assert_called_once_with(
            database_config=self.database_config,
            task_server_config=self.task_server_config,
        )
        self.file_handle.write.assert_not_called()

    def test_generate_config__overwrite(self):
        """[CLT] Generate config - force overwrite"""
        self.open.return_value = self._FakeContextManager(self.file_handle)

        self._run(["generate-config", "-o", self.CONFIG_FILE, "-f"])

        self.open.assert_called_once_with(self.CONFIG_FILE, "w")
        self.config.generate.assert_called_once_with(
            database_config=self.database_config,
            task_server_config=self.task_server_config,
        )
        self.file_handle.write.assert_called_once_with(self.TOML_CONFIG)

    @mock.patch.object(clt, "print")
    def test_generate_config__different_output(self, print_):
        """[CLT] Generate config, print to std out"""
        self.open.return_value = self._FakeContextManager(self.file_handle)

        self._run(["generate-config"])

        self.config.generate.assert_called_once_with(
            database_config=self.database_config,
            task_server_config=self.task_server_config,
        )
        print_.assert_called_once_with(self.TOML_CONFIG)

    def test_generate_config__custom_values(self):
        """[CLT] Generate config using current values"""
        self.open.return_value = self._FakeContextManager(self.file_handle)

        self._run(["generate-config", "-o", self.CONFIG_FILE, "-u"])

        self.open.assert_called_once_with(self.CONFIG_FILE, "x")
        self.config.generate.assert_called_once_with()
        self.file_handle.write.assert_called_once_with(self.TOML_CONFIG)

    def test_rebuild_db(self):
        """[CLT] Rebuild DB"""
        self._run(["rebuild-db", "--yes"])

        self.database.rebuild_db.assert_called_once_with()

    def test_rebuild_db_require_verification(self):
        """[CLT] Rebuild DB - requires verification"""
        self._run(["rebuild-db"])

        self.database.rebuild_db.assert_not_called()

    def _run(self, options):
        return self.runner.invoke(clt.transiter_clt, options)
