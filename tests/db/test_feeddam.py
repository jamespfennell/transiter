import datetime

from transiter import models
from transiter.data.dams import feeddam
from . import dbtestutil, testdata


class TestFeedDAM(dbtestutil.TestCase):
    def test_list_all_in_system(self):
        """[Feed DAM] List all in system"""
        self.assertListEqual(
            [testdata.feed_one, testdata.feed_two],
            feeddam.list_all_in_system(testdata.SYSTEM_ONE_ID),
        )

    def test__feeddam__get_in_system_by_id(self):
        """[Feed DAM] Get in system by ID"""
        self.assertEqual(
            testdata.feed_one,
            feeddam.get_in_system_by_id(testdata.SYSTEM_ONE_ID, testdata.FEED_ONE_ID),
        )

    def test_list_all_auto_updated(self):
        """[Feed DAM] List all auto updated"""
        self.assertListEqual(
            [testdata.feed_one, testdata.feed_3], feeddam.list_all_autoupdating()
        )

    def test__feed_dao__get_last_successful_update(self):
        """[Feed DAM] Last successful update"""
        self.assertEqual(
            testdata.feed_1_update_2,
            feeddam.get_last_successful_update(testdata.FEED_ONE_PK),
        )

    def test_get_last_successful_update__no_update(self):
        """[Feed DAM] Last successful update - no update"""
        self.assertEqual(None, feeddam.get_last_successful_update(testdata.FEED_TWO_PK))

    def test_list_updates_in_feed(self):
        """[Feed DAM] List updates in feed"""
        self.assertEqual(
            [
                testdata.feed_1_update_3,
                testdata.feed_1_update_2,
                testdata.feed_1_update_1,
            ],
            feeddam.list_updates_in_feed(testdata.FEED_ONE_PK),
        )

    def test_trim_updates(self):
        """[Feed DAM] Trim updates"""
        feeddam.trim_feed_updates(datetime.datetime(2011, 1, 1, 1, 30, 0))

        self.assertEqual(
            [testdata.feed_1_update_3, testdata.feed_1_update_2],
            feeddam.list_updates_in_feed(testdata.FEED_ONE_PK),
        )

    def test_aggregate_updates(self):
        """[Feed DAM] Aggregate updates"""
        expected = [
            (
                testdata.SYSTEM_ONE_ID,
                testdata.FEED_ONE_ID,
                models.FeedUpdate.Status.SUCCESS,
                None,
                1,
                None,
            )
        ]

        actual = feeddam.aggregate_feed_updates(datetime.datetime(2011, 1, 1, 1, 30, 0))

        self.assertEqual(expected, actual)
