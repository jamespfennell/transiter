from unittest import mock

import requests

from transiter import models
from transiter.services.update import updatemanager
from ... import testutil


class TestUpdateManager(testutil.TestCase(updatemanager)):
    FEED_ID = "1"
    SYSTEM_ID = "2"
    MODULE_NAME = "module"
    METHOD_NAME = "method"
    CUSTOM_PARSER = "{}:{}".format(MODULE_NAME, METHOD_NAME)
    URL = "http://www.feed.com"
    FEED_CONTENT = "BlahBah"
    OLD_FEED_CONTENT = "BlahBah2"

    class GoodModule:
        method = mock.MagicMock()

    class BadModule:
        pass

    def setUp(self):
        self.requests = self.mockImportedModule(updatemanager.requests)
        self.response = mock.MagicMock()
        self.requests.get.return_value = self.response
        self.response.content = self.FEED_CONTENT.encode("utf-8")

        self.importlib = self.mockImportedModule(updatemanager.importlib)
        self.traceback = self.mockImportedModule(updatemanager.traceback)
        self.dbconnection = self.mockImportedModule(updatemanager.dbconnection)

        self.built_in_parser = mock.MagicMock()
        updatemanager._built_in_parser_to_function[
            models.Feed.BuiltInParser.GTFS_REALTIME
        ] = self.built_in_parser

        self.system = models.System(id=self.SYSTEM_ID)
        self.feed = models.Feed(id=self.FEED_ID, system=self.system)
        self.feed_update = models.FeedUpdate(self.feed)

        self.feeddam = self.mockImportedModule(updatemanager.feeddam)
        self.old_feed_update = models.FeedUpdate(self.feed)
        self.old_feed_update.raw_data_hash = updatemanager._calculate_content_hash(
            self.OLD_FEED_CONTENT.encode("utf-8")
        )
        self.feeddam.get_last_successful_update.return_value = self.old_feed_update

    def test_execute_feed_update__success(self):
        """[Update manager] execute feed update - success"""
        self.feed.built_in_parser = self.feed.BuiltInParser.GTFS_REALTIME

        updatemanager.execute_feed_update(self.feed_update)

        self.assertEqual(self.feed_update.status, self.feed_update.Status.SUCCESS)
        self.assertEqual(
            self.feed_update.explanation, self.feed_update.Explanation.UPDATED
        )

    def test_execute_feed_update__not_needed(self):
        """[Update manager] execute feed update - not needed"""
        self.feed.built_in_parser = self.feed.BuiltInParser.GTFS_REALTIME
        self.response.content = self.OLD_FEED_CONTENT.encode("utf-8")

        updatemanager.execute_feed_update(self.feed_update)

        self.assertEqual(self.feed_update.status, self.feed_update.Status.SUCCESS)
        self.assertEqual(
            self.feed_update.explanation, self.feed_update.Explanation.NOT_NEEDED
        )

    def test_execute_feed_update__invalid_parser(self):
        """[Update manager] execute feed update - invalid parser"""

        self.feed.custom_parser = "no_colon_here"

        updatemanager.execute_feed_update(self.feed_update)

        self.assertEqual(self.feed_update.status, self.feed_update.Status.FAILURE)
        self.assertEqual(
            self.feed_update.explanation, self.feed_update.Explanation.INVALID_PARSER
        )

    def test_execute_feed_update__download_error(self):
        """[Update manager] execute feed update - download error"""
        self.feed.built_in_parser = self.feed.BuiltInParser.GTFS_REALTIME

        self.response.raise_for_status.side_effect = requests.RequestException

        updatemanager.execute_feed_update(self.feed_update)

        self.assertEqual(self.feed_update.status, self.feed_update.Status.FAILURE)
        self.assertEqual(
            self.feed_update.explanation, self.feed_update.Explanation.DOWNLOAD_ERROR
        )

    def test_execute_feed_update__parse_error(self):
        """[Update manager] execute feed update - parse error"""
        self.feed.built_in_parser = self.feed.BuiltInParser.GTFS_REALTIME

        self.built_in_parser.side_effect = ValueError

        updatemanager.execute_feed_update(self.feed_update)

        self.assertEqual(self.feed_update.status, self.feed_update.Status.FAILURE)
        self.assertEqual(
            self.feed_update.explanation, self.feed_update.Explanation.PARSE_ERROR
        )

    def test_get_parser__invalid_parser_string(self):
        """[Update manager] Get parser - invalid custom parser string"""
        self.feed.custom_parser = "no_colon_here"

        self.assertRaises(
            updatemanager._InvalidParser, lambda: updatemanager._get_parser(self.feed)
        )

    def test_get_parser__invalid_module(self):
        """[Update manager] Get parser - no such module"""
        self.feed.custom_parser = self.CUSTOM_PARSER

        self.importlib.import_module.side_effect = ModuleNotFoundError

        self.assertRaises(
            updatemanager._InvalidParser, lambda: updatemanager._get_parser(self.feed)
        )

        self.importlib.import_module.assert_has_calls(
            [mock.call(self.MODULE_NAME), mock.call(self.MODULE_NAME)]
        )
        self.importlib.invalidate_caches.assert_called_once_with()

    def test_get_parser__cache_refresh_needed(self):
        """[Update manager] Get parser - cache refresh required"""
        self.feed.custom_parser = self.CUSTOM_PARSER

        # This is a hack to get around the seeming fact that functions passed
        # to side_effect cannot use the keyword global to access stuff in the
        # outer scope. So instead we use storage to hold the global scope and
        # have both importlib functions call this function, so they both get
        # access to the storage.
        def import_lib_function(argument=None, storage=[]):
            if argument is None:  # invalidate_caches
                storage.append(1)
                return
            if len(storage) > 0:
                return self.GoodModule()
            else:
                raise ModuleNotFoundError

        self.importlib.import_module.side_effect = import_lib_function
        self.importlib.invalidate_caches.side_effect = import_lib_function

        method = updatemanager._get_parser(self.feed)

        self.assertEqual(method, self.GoodModule.method)

        self.importlib.import_module.assert_has_calls(
            [mock.call(self.MODULE_NAME), mock.call(self.MODULE_NAME)]
        )
        self.importlib.invalidate_caches.assert_called_once_with()

    def test_get_parser__invalid_method(self):
        """[Update manager] Get parser - invalid method"""
        self.feed.custom_parser = self.CUSTOM_PARSER

        self.importlib.import_module.return_value = self.BadModule()

        self.assertRaises(
            updatemanager._InvalidParser, lambda: updatemanager._get_parser(self.feed)
        )

        self.importlib.import_module.assert_called_once_with(self.MODULE_NAME)
        self.importlib.invalidate_caches.assert_not_called()

    def test_get_parser__success(self):
        """[Update manager] Get parser - success"""
        self.feed.custom_parser = self.CUSTOM_PARSER

        self.importlib.import_module.return_value = self.GoodModule()

        method = updatemanager._get_parser(self.feed)

        self.assertEqual(method, self.GoodModule.method)

        self.importlib.import_module.assert_called_once_with(self.MODULE_NAME)
        self.importlib.invalidate_caches.assert_not_called()

    def test_all_built_in_parsers_defined(self):
        """[Update manager] All built in parsers defined"""
        for built_in_parser in models.Feed.BuiltInParser:
            self.assertTrue(
                built_in_parser in updatemanager._built_in_parser_to_function
            )
