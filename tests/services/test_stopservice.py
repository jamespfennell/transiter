import unittest
import unittest.mock as mock

from transiter.services import stopservice


class TestStopService(unittest.TestCase):

    SYSTEM_ID = '1'
    STOP_ONE_ID = '2'
    STOP_ONE_REPR = {'stop_id': STOP_ONE_ID}

    def _quick_mock(self, name):
        cache_name = '_quick_mock_cache_{}'.format(name)
        self.__setattr__(cache_name, mock.patch(
            'transiter.services.stopservice.{}'.format(name)))
        mocked = getattr(self, cache_name).start()
        self.addCleanup(getattr(self, cache_name).stop)
        return mocked

    def setUp(self):
        self.linksutil = self._quick_mock('linksutil')
        self.stop_dao = self._quick_mock('stop_dao')

        self.stop_one = mock.MagicMock()
        self.stop_one.short_repr.return_value = self.STOP_ONE_REPR
        self.stop_one_href = mock.MagicMock()
        self.stop_dao.list_all_in_system.return_value = [
            self.stop_one]

        self.linksutil.StopEntityLink.return_value = self.stop_one_href

    def test_list_all_in_system(self):
        expected = [
            {
                'href': self.stop_one_href,
                **self.STOP_ONE_REPR
            }
        ]

        actual = stopservice.list_all_in_system(self.SYSTEM_ID)

        self.assertListEqual(actual, expected)
        self.stop_one.short_repr.assert_called_once_with()
        self.linksutil.StopEntityLink.assert_called_once_with(self.stop_one)
        self.stop_dao.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

