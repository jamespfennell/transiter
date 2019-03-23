import unittest
import unittest.mock as mock

from transiter.services import feedservice


class TestFeedService(unittest.TestCase):

    SYSTEM_ID = '1'
    FEED_ONE_ID = '2'
    FEED_ONE_REPR = {'feed_id': FEED_ONE_ID}
    FEED_UPDATE_ONE_REPR = {'id': '4'}

    def _quick_mock(self, name):
        cache_name = '_quick_mock_cache_{}'.format(name)
        self.__setattr__(cache_name, mock.patch(
            'transiter.services.feedservice.{}'.format(name)))
        mocked = getattr(self, cache_name).start()
        self.addCleanup(getattr(self, cache_name).stop)
        return mocked

    def setUp(self):
        #self.importlib = self._quick_mock('importlib')
        #self.hashlib = self._quick_mock('hashlib')
        #self.requests = self._quick_mock('requests')
        self.linksutil = self._quick_mock('linksutil')
        self.feed_dao = self._quick_mock('feeddam')

        self.feed_one = mock.MagicMock()
        self.feed_one.short_repr.return_value = self.FEED_ONE_REPR
        self.feed_one_href = mock.MagicMock()
        self.feed_one.parser = 'custom'
        self.feed_one.custom_function = 'custom_function'
        self.feed_dao.list_all_in_system.return_value = [
            self.feed_one]
        self.feed_dao.get_in_system_by_id.return_value = self.feed_one

        self.feed_update_one = mock.MagicMock()
        self.feed_update_one.short_repr.return_value = self.FEED_UPDATE_ONE_REPR
        self.feed_dao.list_updates_in_feed.return_value = [
            self.feed_update_one]
        self.feed_update_two = mock.MagicMock()
        self.feed_update_two.feed = self.feed_one
        self.feed_dao.get_last_successful_update.return_value = self.feed_update_one

        self.linksutil.FeedEntityLink.return_value = self.feed_one_href

        """
        m = mock.MagicMock()
        self.hashlib.md5.return_value = m
        m.hexdigest.return_value = 'HASH2'

        self.module = mock.MagicMock()
        self.importlib.import_module.return_value = self.module
        self.module.custom_function = mock.MagicMock()

        self.request = mock.MagicMock()
        self.requests.get.return_value = self.request
        """


    def test_list_all_in_system(self):
        """[Feed service] List all in system"""
        expected = [
            {
                **self.FEED_ONE_REPR,
                'href': self.feed_one_href,
            }
        ]

        actual = feedservice.list_all_in_system(self.SYSTEM_ID)

        self.assertListEqual(actual, expected)
        self.feed_one.short_repr.assert_called_once_with()
        self.linksutil.FeedEntityLink.assert_called_once_with(self.feed_one)
        self.feed_dao.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

    def test_get_in_system_by_id(self):
        expected = {
            **self.FEED_ONE_REPR,
        }

        actual = feedservice.get_in_system_by_id(self.SYSTEM_ID, self.FEED_ONE_ID)
        del actual['updates']

        self.assertDictEqual(actual, expected)

        self.feed_one.short_repr.assert_called_once_with()
        self.feed_dao.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID)

    @mock.patch('transiter.services.feedservice.updatemanager.execute_feed_update')
    def _test_create_feed_update(self, _execute_feed_update):
        feed_update = mock.MagicMock()
        self.feed_dao.create_update.return_value = feed_update
        expected = {
        }

        actual = feedservice.create_feed_update(self.SYSTEM_ID, self.FEED_ONE_ID)

        self.assertDictEqual(actual, expected)
        self.assertEqual(feed_update.feed, self.feed_one)
        self.assertEqual(feed_update.status, 'SCHEDULED')

        self.feed_dao.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID)
        _execute_feed_update.assert_called_once_with(feed_update)

    def test_list_updates_in_feed(self):
        expected = [
            self.FEED_UPDATE_ONE_REPR
        ]

        actual = feedservice.list_updates_in_feed(self.SYSTEM_ID, self.FEED_ONE_ID)

        self.assertListEqual(actual, expected)
        self.feed_dao.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID)
        self.feed_dao.list_updates_in_feed.assert_called_once_with(
            self.feed_one)

    def _test_execute_feed_update_success(self):
        self.feed_update_one.raw_data_hash = 'HASH1'

        feedservice._execute_feed_update(self.feed_update_two)

        self.assertEqual(self.feed_update_two.status, 'SUCCESS')
        self.module.custom_function.assert_called_once_with(
            self.feed_one, self.request.content)

    def _test_execute_feed_update_not_needed(self):
        self.feed_update_one.raw_data_hash = 'HASH2'

        feedservice._execute_feed_update(self.feed_update_two)

        self.assertEqual(self.feed_update_two.status, 'SUCCESS')
        self.module.custom_function.assert_not_called()

    def _test_execute_feed_update_failure(self):
        self.feed_update_one.raw_data_hash = 'HASH1'
        self.module.custom_function.side_effect = Exception

        feedservice._execute_feed_update(self.feed_update_two)

        self.assertEqual(self.feed_update_two.status, 'FAILURE')
        self.module.custom_function.assert_called_once_with(
            self.feed_one, self.request.content)
