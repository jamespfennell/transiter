from transiter.import_ import fastscheduleoperations


def test_split():
    expected = [[7, 8, 9], [1, 2, 3], [6]]
    container = sum(expected, [])

    actual = list(fastscheduleoperations.split(container, 3))

    assert expected == actual


def test_split_2():
    expected = [[7, 8, 9], [1, 2, 3]]
    container = sum(expected, [])

    actual = list(fastscheduleoperations.split(container, 3))

    assert expected == actual


def test_split_3():
    expected = []
    container = []

    actual = list(fastscheduleoperations.split(container, 3))

    assert expected == actual
