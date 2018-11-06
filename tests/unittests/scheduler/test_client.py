import unittest
import unittest.mock as mock
from transiter.scheduler import client


class TestClient(unittest.TestCase):

    RESPONSE = '1'

    @mock.patch('transiter.scheduler.client.rpyc')
    def test_content(self, rpyc):
        """[RPYC Scheduler] Client get success"""
        conn = mock.MagicMock()
        conn.root.refresh_jobs.return_value = self.RESPONSE
        rpyc.connect.return_value = conn

        response = client.refresh_jobs()

        self.assertEqual(self.RESPONSE, response)

        rpyc.connect.assert_called_once_with('localhost', 12345)
        conn.root.refresh_jobs.assert_called_once_with()

    @mock.patch('transiter.scheduler.client.rpyc')
    def test_fail_to_connect(self, rpyc):
        """[RPYC Scheduler] Client failure to connect"""
        rpyc.connect.side_effect = ConnectionRefusedError

        response = client.refresh_jobs()

        self.assertEqual(False, response)

        rpyc.connect.assert_called_once_with('localhost', 12345)
