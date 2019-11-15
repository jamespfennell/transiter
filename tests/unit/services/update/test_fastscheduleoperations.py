from transiter.services.update import fastscheduleoperations


from ... import testutil


class TestFastScheduleOperations(testutil.TestCase(fastscheduleoperations)):
    def test_split(self):
        """
        [Fast schedule operations] Split list
        """
        expected = [[7, 8, 9], [1, 2, 3], [6]]
        container = sum(expected, [])

        actual = list(fastscheduleoperations.split(container, 3))

        assert expected == actual

    def test_split_2(self):
        """
        [Fast schedule operations] Split list 2
        """
        expected = [[7, 8, 9], [1, 2, 3]]
        container = sum(expected, [])

        actual = list(fastscheduleoperations.split(container, 3))

        assert expected == actual

    def test_split_3(self):
        """
        [Fast schedule operations] Split list, empty list
        """
        expected = []
        container = []

        actual = list(fastscheduleoperations.split(container, 3))

        assert expected == actual
