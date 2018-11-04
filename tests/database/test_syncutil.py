import unittest
from unittest import mock

from transiter.database import syncutil
from transiter.database import models

class TestSync(unittest.TestCase):

    ID_ONE = 4
    ID_TWO = 5
    ID_THREE = 6
    OLD_VALUE_ONE = "1"
    OLD_VALUE_TWO = "2"
    NEW_VALUE_TWO = "3"
    NEW_VALUE_THREE = "4"

    class MockDbModel:

        def __init__(self, id=None, value=None):
            self.id = id
            self.key = value

        def __eq__(self, other):
            return self.__dict__ == other.__dict__

        def __hash__(self):
            return hash(str(self))

        def __str__(self):
            return str(self.__dict__)

        def __repr__(self):
            return str(self)

    @mock.patch('transiter.database.syncutil.connection')
    def test_sync(self, connection):
        """[Database sync] Sync data"""

        def add_function(entity):
            self._new_entities.add(entity)

        def delete_function(session, entity):
            self._deleted_entities.add(entity)

        session = mock.MagicMock()
        connection.get_session.return_value = session
        session.add.side_effect = add_function

        self._new_entities = set()
        self._deleted_entities = set()

        old_one = self.MockDbModel(self.ID_ONE, self.OLD_VALUE_ONE)
        old_two = self.MockDbModel(self.ID_TWO, self.OLD_VALUE_TWO)
        new_two = self.MockDbModel(self.ID_TWO, self.NEW_VALUE_TWO)
        new_three = self.MockDbModel(self.ID_THREE, self.NEW_VALUE_THREE)
        db_entities = [old_one, old_two]
        expected_new_db_entities = [new_two, new_three]
        new_entities = [
            {
                'id': self.ID_TWO,
                'key': self.NEW_VALUE_TWO
            },
            {
                'id': self.ID_THREE,
                'key': self.NEW_VALUE_THREE
            }
        ]

        actual_new_db_entities = syncutil.sync(
            self.MockDbModel, db_entities, new_entities, ['id'], delete_function)

        self.assertListEqual(actual_new_db_entities, expected_new_db_entities)
        self.assertSetEqual(self._deleted_entities, {old_one})
        # NOTE: Unittest's assertSetEqual uses set.difference() which does
        # note use the obj.__eq__ method, so sets containing objects with the
        # the same data fail the assertion
        self.assertListEqual(list(self._new_entities), [new_three])

    def _session_add(self, entity):
        self._new_entities.add(entity)


class TestTripSync(unittest.TestCase):

    ROUTE_ONE_ID = '1'
    ROUTE_ONE_PK = 2
    ROUTE_TWO_ID = '3'
    SYSTEM_ID = '4'
    TRIP_PK = 5
    STOP_ONE_ID = '6'
    STOP_ONE_PK = 7
    STOP_TWO_ID = '8'
    STOP_TWO_PK = 9
    STOP_TWO_ID_ALIAS = '10'
    STOP_THREE_ID = '11'
    TRIP_ONE_ID = '12'
    TRIP_ONE_PK = 12
    TRIP_TWO_ID = '13'
    TRIP_TWO_PK = 14

    @mock.patch('transiter.database.syncutil.sync')
    @mock.patch('transiter.database.syncutil.trip_dao')
    @mock.patch('transiter.database.syncutil.route_dao')
    def test_persist_trips(self, route_dao, trip_dao, sync):
        new_trips = [
            {
                'route_id': self.ROUTE_ONE_ID,
                'stop_events': mock.MagicMock()
            },
            {
                'route_id': self.ROUTE_TWO_ID
            }
        ]
        new_trips_to_persist = [
            {
                'route_pri_key': self.ROUTE_ONE_PK
            }
        ]

        route_id_to_route_pk = {
            self.ROUTE_ONE_ID: self.ROUTE_ONE_PK
        }
        route_dao.get_id_to_pk_map.return_value = route_id_to_route_pk

        old_trips = mock.MagicMock()
        trip_dao.list_all_in_routes_by_pk.return_value = old_trips

        persisted_trips = mock.MagicMock()
        sync.return_value = persisted_trips

        actual = syncutil._persist_trips(
            self.SYSTEM_ID,
            [self.ROUTE_ONE_ID, self.ROUTE_TWO_ID],
            new_trips
        )

        self.assertEqual(persisted_trips, actual)
        self.assertFalse('stop_events' in new_trips[0])

        route_dao.get_id_to_pk_map.assert_called_once_with(
            self.SYSTEM_ID, [self.ROUTE_ONE_ID, self.ROUTE_TWO_ID])
        trip_dao.list_all_in_routes_by_pk.assert_called_once_with(
            [self.ROUTE_ONE_PK])
        sync.assert_called_once_with(
            models.Trip,
            old_trips,
            new_trips_to_persist,
            ['route_pri_key', 'trip_id']
        )

    @mock.patch('transiter.database.syncutil.sync')
    @mock.patch('transiter.database.syncutil.archive_function_factory')
    def test_persist_stop_events(self, archive_function_factory, sync):
        old_stop_events = mock.MagicMock()
        new_stop_events = [
            {
                'stop_id': self.STOP_THREE_ID,
                'stop_sequence': 3,
            },
            {
                'stop_id': self.STOP_ONE_ID,
                'stop_sequence': 4,
            },
            {
                'stop_id': self.STOP_TWO_ID_ALIAS,
                'stop_sequence': 5,
            },
        ]
        new_stop_events_post = [
            None,
            {
                'stop_pri_key': self.STOP_ONE_PK,
                'stop_sequence': 4,
                'future': True,
                'trip_pri_key': self.TRIP_PK
            },
            {
                'stop_pri_key': self.STOP_TWO_PK,
                'stop_sequence': 5,
                'future': True,
                'trip_pri_key': self.TRIP_PK,
                'stop_id_alias': self.STOP_TWO_ID_ALIAS
            },
        ]
        stop_id_alias_to_stop_id = {
            self.STOP_TWO_ID_ALIAS: self.STOP_TWO_ID
        }
        stop_id_to_stop_pk = {
            self.STOP_ONE_ID: self.STOP_ONE_PK,
            self.STOP_TWO_ID: self.STOP_TWO_PK
        }
        archive_function = mock.MagicMock()
        archive_function_factory.return_value = archive_function

        result = syncutil._persist_stop_events(
            self.TRIP_PK,
            old_stop_events,
            new_stop_events,
            stop_id_alias_to_stop_id,
            stop_id_to_stop_pk
        )

        self.assertSetEqual({self.STOP_THREE_ID}, result)

        archive_function_factory.assert_called_once_with(4)
        sync.assert_called_once_with(
            models.StopEvent,
            old_stop_events,
            new_stop_events_post,
            ['stop_pri_key'],
            delete_function=archive_function
        )

    @mock.patch('transiter.database.syncutil._persist_trips')
    @mock.patch('transiter.database.syncutil._persist_stop_events')
    @mock.patch('transiter.database.syncutil.trip_dao')
    @mock.patch('transiter.database.syncutil.stop_dao')
    def test_sync_trips(self, stop_dao, trip_dao, _persist_stop_events, _persist_trips):
        stop_events_one = [
            {
                'stop_id': self.STOP_ONE_ID,
            },
            {
                'stop_id': self.STOP_TWO_ID,
            }
        ]
        stop_events_two = [
            {
                'stop_id': self.STOP_THREE_ID,
            },
            {
                'stop_id': self.STOP_TWO_ID_ALIAS,
            }
        ]
        trips = [
            {
                'route_id': self.ROUTE_ONE_ID,
                'trip_id': self.TRIP_ONE_ID,
                'stop_events': stop_events_one
            },
            {
                'route_id': self.ROUTE_ONE_ID,
                'trip_id': self.TRIP_TWO_ID,
                'stop_events': stop_events_two
            }
        ]
        data = {
            'route_ids': [self.ROUTE_ONE_ID, self.ROUTE_TWO_ID],
            'trips': trips
        }

        db_trip_data = [mock.MagicMock()]
        trip_pk_to_db_stop_events = {
            self.TRIP_ONE_PK: db_trip_data
        }
        trip_dao.get_trip_pk_to_future_stop_events_map.return_value = (
            trip_pk_to_db_stop_events)

        pt_one = mock.MagicMock()
        pt_one.id = self.TRIP_ONE_PK
        pt_one.trip_id = self.TRIP_ONE_ID
        pt_one.route_id = self.ROUTE_ONE_ID
        pt_two = mock.MagicMock()
        pt_two.id = self.TRIP_TWO_PK
        pt_two.trip_id = self.TRIP_TWO_ID
        pt_two.route_id = self.ROUTE_ONE_ID
        persisted_trips = [pt_one, pt_two]
        _persist_trips.return_value = persisted_trips

        stop_id_alias_to_stop_id = {self.STOP_TWO_ID_ALIAS: self.STOP_TWO_ID}
        stop_dao.get_stop_id_alias_to_stop_id_map.return_value = stop_id_alias_to_stop_id
        stop_id_to_stop_pk = mock.MagicMock()
        stop_dao.get_id_to_pk_map.return_value = stop_id_to_stop_pk

        syncutil.sync_trips(data, self.SYSTEM_ID)

        _persist_trips.assert_called_once_with(
            self.SYSTEM_ID,
            data['route_ids'],
            trips)
        trip_dao.get_trip_pk_to_future_stop_events_map.assert_called_once_with(
            [self.TRIP_ONE_PK, self.TRIP_TWO_PK])
        stop_dao.get_stop_id_alias_to_stop_id_map.assert_called_once_with(
            self.SYSTEM_ID,
            {self.STOP_THREE_ID, self.STOP_ONE_ID, self.STOP_TWO_ID_ALIAS, self.STOP_TWO_ID})
        stop_dao.get_id_to_pk_map()
        _persist_stop_events.assert_any_call(
            self.TRIP_ONE_PK,
            stop_events_one,
            db_trip_data,
            stop_id_alias_to_stop_id,
            stop_id_to_stop_pk
        )
        _persist_stop_events.assert_any_call(
            self.TRIP_TWO_PK,
            stop_events_two,
            [],
            stop_id_alias_to_stop_id,
            stop_id_to_stop_pk
        )
        self.assertEqual(2, _persist_stop_events.call_count)

    def test_archive_function_factory(self):
        archive_function = syncutil.archive_function_factory(3)

        session = mock.MagicMock()
        stop_event_one = models.StopEvent()
        stop_event_one.sequence_index = 2
        stop_event_one.future = True
        stop_event_two = models.StopEvent()
        stop_event_two.sequence_index = 4
        stop_event_two.future = True

        archive_function(session, stop_event_one)
        archive_function(session, stop_event_two)

        session.delete.assert_called_once_with(stop_event_two)
        self.assertFalse(stop_event_one.future)

