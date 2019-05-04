import unittest
import unittest.mock as mock
from transiter.taskserver import client


class TestClient(unittest.TestCase):

    RESPONSE = "1"

    @mock.patch("transiter.taskserver.client.rpyc")
    def test_content(self, rpyc):
        """[RPYC Scheduler] Client get success"""
        conn = mock.MagicMock()
        conn.root.refresh_tasks.return_value = self.RESPONSE
        rpyc.connect.return_value = conn

        response = client.refresh_tasks()

        self.assertEqual(self.RESPONSE, response)

        rpyc.connect.assert_called_once()
        conn.root.refresh_tasks.assert_called_once_with()

    @mock.patch("transiter.taskserver.client.rpyc")
    def test_fail_to_connect(self, rpyc):
        """[RPYC Scheduler] Client failure to connect"""
        rpyc.connect.side_effect = ConnectionRefusedError

        response = client.refresh_tasks()

        self.assertEqual(False, response)

        rpyc.connect.assert_called_once()
