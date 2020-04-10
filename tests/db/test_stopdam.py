import datetime

from transiter.data.dams import stopdam


def test_list_all_in_system(system_1, stop_1_1, stop_1_2, stop_2_1):
    assert [stop_1_1, stop_1_2] == stopdam.list_all_in_system(system_1.id)


def test_list_all_in_system__no_stops(system_1, stop_2_1):
    assert [] == stopdam.list_all_in_system(system_1.id)


def test_list_all_in_system__no_system(system_1):
    assert [] == stopdam.list_all_in_system("unknown_id")


def test_get_in_system_by_id(system_1, stop_1_1, stop_1_2):
    assert stop_1_2 == stopdam.get_in_system_by_id(system_1.id, stop_1_2.id)


def test_get_in_system_by_id__no_stop(system_1, stop_1_1, stop_1_2):
    assert None is stopdam.get_in_system_by_id(system_1.id, "unknown_id")


def test_get_in_system_by_id__no_system(system_1, stop_1_1, stop_1_2):
    assert None is stopdam.get_in_system_by_id("unknown_id", stop_1_2.id)


def test_get_id_to_pk_map_in_system(system_1, stop_1_1, stop_1_2, stop_2_1):
    expected = {
        stop_1_1.id: stop_1_1.pk,
        stop_2_1.id: None,
        "unknown_id": None,
    }

    actual = stopdam.get_id_to_pk_map_in_system(system_1.pk, expected.keys())

    assert expected == actual


def test_get_id_to_pk_map_in_system__all_stops(system_1, stop_1_1, stop_1_2, stop_2_1):
    expected = {
        stop_1_1.id: stop_1_1.pk,
        stop_1_2.id: stop_1_2.pk,
    }

    actual = stopdam.get_id_to_pk_map_in_system(system_1.pk)

    assert expected == actual


def test_list_stop_time_updates_at_stops__no_stop_times(
    stop_1_4, trip_1, trip_2, trip_3
):
    actual_stop_times = stopdam.list_stop_time_updates_at_stops([])

    assert [] == actual_stop_times


def test_list_stop_time_updates_at_stops(stop_1_4, trip_1, trip_2, trip_3):
    actual_stop_times = stopdam.list_stop_time_updates_at_stops([stop_1_4.pk])
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_1, trip_2, trip_3] == actual_trips


def test_list_stop_time_updates_at_stops__earliest_time(
    stop_1_4, trip_1, trip_2, trip_3
):
    actual_stop_times = stopdam.list_stop_time_updates_at_stops(
        [stop_1_4.pk], earliest_time=datetime.datetime(2018, 11, 2, 10, 30, 0)
    )
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_2, trip_3] == actual_trips


def test_list_stop_time_updates_at_stops__latest_time(stop_1_4, trip_1, trip_2, trip_3):
    actual_stop_times = stopdam.list_stop_time_updates_at_stops(
        [stop_1_4.pk], latest_time=datetime.datetime(2018, 11, 2, 11, 30, 0)
    )
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_1, trip_2] == actual_trips


def test_list_stop_time_updates_at_stops__earliest_and_latest_time(
    stop_1_4, trip_1, trip_2, trip_3
):
    actual_stop_times = stopdam.list_stop_time_updates_at_stops(
        [stop_1_4.pk],
        earliest_time=datetime.datetime(2018, 11, 2, 10, 30, 0),
        latest_time=datetime.datetime(2018, 11, 2, 11, 30, 0),
    )
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_2] == actual_trips


def test_get_stop_pk_to_station_pk(
    system_1, stop_1_1, stop_1_2, stop_1_3, stop_1_4, stop_2_1
):
    expected = {
        stop_1_1.pk: stop_1_1.pk,
        stop_1_2.pk: stop_1_2.pk,
        stop_1_3.pk: stop_1_2.pk,
        stop_1_4.pk: stop_1_4.pk,
    }

    actual = stopdam.get_stop_pk_to_station_pk_map_in_system(system_1.id)

    assert expected == actual
