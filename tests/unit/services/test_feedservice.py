import unittest

from transiter.services import feedservice, links
from transiter import models, exceptions
from .. import testutil


class TestFeedService(testutil.TestCase(feedservice), unittest.TestCase):

    SYSTEM_ID = "1"
    FEED_ONE_ID = "2"
    FEED_ONE_PK = 3
    FEED_ONE_AUTO_UPDATE_PERIOD = 500
    FEED_TWO_ID = "4"

    def setUp(self):
        self.feeddam = self.mockImportedModule(feedservice.feeddam)
        self.systemdam = self.mockImportedModule(feedservice.systemdam)
        self.updatemanager = self.mockImportedModule(feedservice.updatemanager)

        self.system = models.System()
        self.system.id = self.SYSTEM_ID

        self.feed_one = models.Feed()
        self.feed_one.pk = self.FEED_ONE_PK
        self.feed_one.id = self.FEED_ONE_ID
        self.feed_one.system = self.system

        self.feed_two = models.Feed()
        self.feed_two.id = self.FEED_TWO_ID

        self.feed_update_one = models.FeedUpdate(self.feed_one)
        self.feed_update_two = models.FeedUpdate(self.feed_one)

    def test_list_all_auto_updating(self):
        """[Feed service] List all auto updating feed in system"""
        self.feed_one.auto_update_period = self.FEED_ONE_AUTO_UPDATE_PERIOD

        self.feeddam.list_all_autoupdating.return_value = [self.feed_one]

        expected = [
            {
                "pk": self.FEED_ONE_PK,
                "id": self.FEED_ONE_ID,
                "system_id": self.SYSTEM_ID,
                "auto_update_period": self.FEED_ONE_AUTO_UPDATE_PERIOD,
            }
        ]

        actual = feedservice.list_all_auto_updating()

        self.assertEqual(expected, actual)

    def test_list_all_in_system(self):
        """[Feed service] List all in system"""
        self.systemdam.get_by_id.return_value = self.system
        self.feeddam.list_all_in_system.return_value = [self.feed_one, self.feed_two]

        expected = [
            {**self.feed_one.short_repr(), "href": links.FeedEntityLink(self.feed_one)},
            {**self.feed_two.short_repr(), "href": links.FeedEntityLink(self.feed_two)},
        ]

        actual = feedservice.list_all_in_system(self.SYSTEM_ID, True)

        self.assertListEqual(actual, expected)

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_ID)
        self.feeddam.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

    def test_list_all_in_system__no_such_system(self):
        """[Feed service] List all in system - no such system"""
        self.systemdam.get_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: feedservice.list_all_in_system(self.SYSTEM_ID),
        )

        self.systemdam.get_by_id.assert_called_once_with(self.SYSTEM_ID)

    def test_get_in_system_by_id(self):
        """[Feed service] Get a feed in a system"""
        self.feeddam.get_in_system_by_id.return_value = self.feed_one

        expected = {
            **self.feed_one.short_repr(),
            "updates": {"href": links.FeedEntityUpdatesLink(self.feed_one)},
        }

        actual = feedservice.get_in_system_by_id(self.SYSTEM_ID, self.FEED_ONE_ID, True)

        self.assertDictEqual(actual, expected)

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )

    def test_get_in_system_by_id__no_such_feed(self):
        """[Feed service] Get a feed in a system - no such feed"""
        self.feeddam.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: feedservice.get_in_system_by_id(self.SYSTEM_ID, self.FEED_ONE_ID),
        )

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )

    def test_create_feed_update(self):
        """[Feed service] Create a feed update"""
        self.feeddam.get_in_system_by_id.return_value = self.feed_one

        expected = {**self.feed_update_one.long_repr()}

        actual = feedservice.create_feed_update(self.SYSTEM_ID, self.FEED_ONE_ID)

        self.assertDictEqual(actual, expected)
        self.assertEqual(self.feed_update_one.feed, self.feed_one)
        self.assertEqual(
            self.feed_update_one.status, models.FeedUpdate.Status.SCHEDULED
        )

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )
        self.updatemanager.execute_feed_update.assert_called_once_with(
            self.feed_update_one, None
        )

    def test_create_feed_update__no_such_feed(self):
        """[Feed service] Create a feed update - no such feed"""
        self.feeddam.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: feedservice.create_feed_update(self.SYSTEM_ID, self.FEED_ONE_ID),
        )

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )

    def test_list_updates_in_feed(self):
        """[Feed service] List updates in a feed"""
        self.feeddam.get_in_system_by_id.return_value = self.feed_one
        self.feeddam.list_updates_in_feed.return_value = [
            self.feed_update_one,
            self.feed_update_two,
        ]

        expected = [
            self.feed_update_one.short_repr(),
            self.feed_update_two.short_repr(),
        ]

        actual = feedservice.list_updates_in_feed(self.SYSTEM_ID, self.FEED_ONE_ID)

        self.assertListEqual(actual, expected)

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )
        self.feeddam.list_updates_in_feed.assert_called_once_with(self.FEED_ONE_PK)

    def test_list_updates_in_feed__no_such_feed(self):
        """[Feed service] List updates in a feed - no such feed"""
        self.feeddam.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: feedservice.list_updates_in_feed(self.SYSTEM_ID, self.FEED_ONE_ID),
        )

        self.feeddam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.FEED_ONE_ID
        )
