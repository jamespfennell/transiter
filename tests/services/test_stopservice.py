import unittest
import unittest.mock as mock

from transiter.services import stopservice
from transiter.database import models


class TestDirectionNamesMatcher(unittest.TestCase):

    STOP_PK = 1
    DIRECTION_NAME = 'Direction Name'

    def setUp(self):
        self.stop = models.Stop()
        self.stop.id = self.STOP_PK

        self.stop_event = models.StopEvent()
        self.stop_event.track = None
        self.stop_event.stop_id_alias = None
        self.stop_event.trip = models.Trip()
        self.stop_event.trip.direction_id = None

        # Note: having the rule as a mock allows us to test interactions
        self.rule = models.DirectionNameRule()
        self.rule.stop_pk = self.STOP_PK
        self.rule.direction_id = None
        self.rule.track = None
        self.rule.stop_id_alias = None
        self.rule.name = self.DIRECTION_NAME

    def test_no_matching_stop_pk(self):
        self.rule.stop_pk = 2
        dnm = stopservice.DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_direction_id(self):
        self.rule.direction_id = True
        dnm = stopservice.DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_track(self):
        self.rule.track = 'Track'
        dnm = stopservice.DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_stop_id_alias(self):
        self.rule.stop_id_alias = 'StopIdAlias'
        dnm = stopservice.DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_match(self):
        dnm = stopservice.DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, self.DIRECTION_NAME)


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

