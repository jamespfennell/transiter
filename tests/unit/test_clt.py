import unittest
from unittest import mock

from click.testing import CliRunner

from transiter import clt
from . import testutil


class TestClr(testutil.TestCase(clt), unittest.TestCase):
    CONFIG_FILE = "my-file.toml"
    TOML_CONFIG = "blah"

    def setUp(self):
        self.taskserver = self.mockImportedModule(clt.taskserver)
        self.database = self.mockImportedModule(clt.dbconnection)
        self.runner = CliRunner()
        patcher = mock.patch.object(clt, "open")
        self.open = patcher.start()
        self.addCleanup(patcher.stop)
        self.file_handle = mock.MagicMock()

    def test_launch_taskserver(self):
        """[CLT] Launch Task Server"""
        self._run(["launch", "task-server"])

        self.taskserver.launch.assert_called_once_with(False)

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
