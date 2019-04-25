"""
Some tests:


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
"""