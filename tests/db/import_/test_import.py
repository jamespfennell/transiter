import dataclasses
import datetime
import itertools

import pytest
import pytz

from transiter import parse
from transiter.db import models
from transiter.import_ import importdriver
from tests.db.data import route_data


class ParserForTesting(parse.parser.CallableBasedParser):
    def __init__(self, entities):
        self.entities = entities
        super().__init__(self.retrieve_entities)
        self.load_content(b"")

    def retrieve_entities(self, content):
        return self.entities


@pytest.fixture
def feed(add_model, system_1):
    return add_model(models.Feed(system=system_1, id="feed", auto_update_enabled=False))


@pytest.fixture
def feed_2(add_model, system_1):
    return add_model(
        models.Feed(system=system_1, id="feed_2", auto_update_enabled=False)
    )


@pytest.fixture
def previous_update(add_model, feed):
    return add_model(models.FeedUpdate(feed=feed))


@pytest.fixture
def current_update(add_model, feed):
    return add_model(models.FeedUpdate(feed=feed))


@pytest.fixture
def other_feed_update(add_model, feed_2):
    return add_model(models.FeedUpdate(feed=feed_2))


new_agency = parse.Agency(id="agency", name="New Agency", timezone="", url="")
new_alert = parse.Alert(
    id="alert", cause=parse.Alert.Cause.DEMONSTRATION, effect=parse.Alert.Effect.DETOUR
)
new_route = parse.Route(id="route", type=parse.Route.Type.RAIL, description="new_route")
new_stop = parse.Stop(
    id="route", name="new stop", latitude=0, longitude=0, type=parse.Stop.Type.STATION
)
new_vehicle = parse.Vehicle(
    id="vehicle", label="new vehicle", current_status=parse.Vehicle.Status.STOPPED_AT
)


@pytest.mark.parametrize(
    "entity_type,previous,current,expected_counts",
    [
        [models.Alert, [], [new_alert], (1, 0, 0)],
        [
            models.Alert,
            [
                models.Alert(
                    id="alert",
                    cause=models.Alert.Cause.DEMONSTRATION,
                    effect=models.Alert.Effect.DETOUR,
                )
            ],
            [new_alert],
            (0, 1, 0),
        ],
        [
            models.Alert,
            [
                models.Alert(
                    id="alert",
                    cause=models.Alert.Cause.DEMONSTRATION,
                    effect=models.Alert.Effect.DETOUR,
                )
            ],
            [],
            (0, 0, 1),
        ],
        [
            models.Route,
            [models.Route(id="route", description="old route")],
            [new_route],
            (0, 1, 0),
        ],
        [models.Route, [], [new_route], (1, 0, 0)],
        [
            models.Route,
            [models.Route(id="route", description="old route")],
            [new_route],
            (0, 1, 0),
        ],
        [
            models.Agency,
            [models.Agency(id="agency", name="old agency", timezone="")],
            [new_agency],
            (0, 1, 0),
        ],
        [models.Agency, [], [new_agency], (1, 0, 0)],
        [
            models.Agency,
            [models.Agency(id="agency", name="old agency", timezone="")],
            [new_agency],
            (0, 1, 0),
        ],
        [
            models.Route,
            [models.Route(id="route", description="old route")],
            [],
            (0, 0, 1),
        ],
        [models.Stop, [], [new_stop], (1, 0, 0)],
        [
            models.Stop,
            [models.Stop(id="route", name="old stop", type=models.Stop.Type.STATION)],
            [new_stop],
            (0, 1, 0),
        ],
        [
            models.Stop,
            [models.Stop(id="route", name="old stop", type=models.Stop.Type.STATION)],
            [],
            (0, 0, 1),
        ],
        [models.Vehicle, [], [new_vehicle], (1, 0, 0)],
        [
            models.Vehicle,
            [
                models.Vehicle(
                    id="vehicle",
                    label="old vehicle",
                    current_status=models.Vehicle.Status.IN_TRANSIT_TO,
                )
            ],
            [new_vehicle],
            (0, 1, 0),
        ],
        [
            models.Vehicle,
            [
                models.Vehicle(
                    id="vehicle",
                    label="old vehicle",
                    current_status=models.Vehicle.Status.IN_TRANSIT_TO,
                )
            ],
            [],
            (0, 0, 1),
        ],
    ],
)
def test_simple_create_update_delete(
    db_session,
    add_model,
    system_1,
    previous_update,
    current_update,
    entity_type,
    previous,
    current,
    expected_counts,
):
    for entity in previous:
        entity.system_pk = system_1.pk
        entity.source = previous_update
        add_model(entity)

    actual_counts = importdriver.run_import(
        current_update.pk, ParserForTesting(current)
    )

    def fields_to_compare(entity):
        if entity_type is models.Route:
            return entity.id, entity.description, entity.source_pk
        if entity_type is models.Stop:
            return entity.id, entity.name, entity.source_pk
        if entity_type is models.Alert:
            return entity.id, entity.cause, entity.effect
        if entity_type is models.Agency:
            return entity.id, entity.name
        if entity_type is models.Vehicle:
            return entity.id, entity.label, entity.current_status
        raise NotImplementedError

    assert set(map(fields_to_compare, current)) == set(
        map(fields_to_compare, db_session.query(entity_type).all())
    )
    assert expected_counts == actual_counts


@pytest.mark.parametrize(
    "parsed_type",
    [
        new_agency,
        new_route,
        new_stop,
        parse.ScheduledService.create_empty("scheduled_service"),
        parse.DirectionRule(id="direction_rule", name="direction_rule"),
        parse.Trip(id="trip_id"),
        new_vehicle,
        new_alert,
    ],
)
def test_duplicate_ids(current_update, parsed_type, route_1_1, stop_1_1):
    if isinstance(parsed_type, parse.Trip):
        parsed_type.route_id = route_1_1.id
    if isinstance(parsed_type, parse.DirectionRule):
        parsed_type.stop_id = stop_1_1.id

    actual_counts = importdriver.run_import(
        current_update.pk, ParserForTesting([parsed_type, parsed_type])
    )

    assert actual_counts == (1, 0, 0)


@pytest.mark.parametrize(
    "old_id_to_parent_id,expected_id_to_parent_id",
    [
        [{}, {"1": "2", "2": None}],
        [{"1": "2", "2": None}, {}],
        [{"1": "2", "2": None}, {"1": None, "2": None}],
        [{"1": "2", "2": None}, {"1": None, "2": "1"}],
        [{"1": "2", "2": "3", "3": None}, {"1": None, "2": "1", "3": "2"}],
        [{"1": "2", "2": None}, {"2": None}],
        [{"1": "2", "2": None}, {"1": None}],
    ],
)
def test_stop__tree_linking(
    db_session,
    system_1,
    add_model,
    previous_update,
    current_update,
    old_id_to_parent_id,
    expected_id_to_parent_id,
):
    stop_id_to_stop = {
        id_: add_model(
            models.Stop(
                id=id_,
                name=id_,
                system=system_1,
                source=previous_update,
                longitude=0,
                latitude=0,
                type=parse.Stop.Type.STATION,
            )
        )
        for id_ in old_id_to_parent_id.keys()
    }
    for id_, parent_id in old_id_to_parent_id.items():
        if parent_id is None:
            continue
        stop_id_to_stop[id_].parent_stop = stop_id_to_stop[parent_id]
    db_session.flush()

    stop_id_to_stop = {
        id_: parse.Stop(
            id=id_, name=id_, longitude=0, latitude=0, type=parse.Stop.Type.STATION
        )
        for id_ in expected_id_to_parent_id.keys()
    }
    for id_, parent_id in expected_id_to_parent_id.items():
        if parent_id is None:
            continue
        stop_id_to_stop[id_].parent_stop = stop_id_to_stop[parent_id]

    importdriver.run_import(
        current_update.pk, ParserForTesting(list(stop_id_to_stop.values()))
    )

    actual_stop_id_parent_id = {}
    for stop in db_session.query(models.Stop).all():
        if stop.parent_stop is not None:
            actual_stop_id_parent_id[stop.id] = stop.parent_stop.id
        else:
            actual_stop_id_parent_id[stop.id] = None

    assert expected_id_to_parent_id == actual_stop_id_parent_id


def test_route__agency_linking(db_session, current_update):
    agency = parse.Agency(id="agency", name="My Agency", timezone="", url="")
    route = parse.Route(id="route", type=parse.Route.Type.RAIL, agency_id="agency")

    importdriver.run_import(current_update.pk, ParserForTesting([route, agency]))

    persisted_route = db_session.query(models.Route).all()[0]

    assert persisted_route.agency is not None


@pytest.mark.parametrize(
    "previous,current,expected_counts",
    [
        [
            [],
            [parse.DirectionRule(name="Rule", id="route", track="new track")],
            (1, 0, 0),
        ],
        [
            [models.DirectionRule(name="Rule", id="route", track="old track")],
            [parse.DirectionRule(name="Rule", id="route", track="new track")],
            (0, 1, 0),
        ],
        [
            [models.DirectionRule(name="Rule", id="route", track="old track")],
            [],
            (0, 0, 1),
        ],
    ],
)
def test_direction_rules(
    db_session,
    add_model,
    stop_1_1,
    previous_update,
    current_update,
    previous,
    current,
    expected_counts,
):
    for rule in previous:
        rule.stop_pk = stop_1_1.pk
        rule.source = previous_update
        add_model(rule)

    expected_entities = list(current)
    for rule in expected_entities:
        rule.stop_pk = stop_1_1.pk

    for rule in current:
        rule.stop_id = stop_1_1.id

    actual_counts = importdriver.run_import(
        current_update.pk, ParserForTesting(current)
    )

    def fields_to_compare(entity):
        return entity.stop_pk, entity.track, entity.source_pk

    assert set(map(fields_to_compare, expected_entities)) == set(
        map(fields_to_compare, db_session.query(models.DirectionRule).all())
    )
    assert expected_counts == actual_counts


def test_schedule(db_session, stop_1_1, route_1_1, previous_update, current_update):
    stop_time = parse.ScheduledTripStopTime(
        stop_id=stop_1_1.id, stop_sequence=3, departure_time=None, arrival_time=None
    )

    trip = parse.ScheduledTrip(
        id="trid_id",
        route_id=route_1_1.id,
        direction_id=True,
        stop_times=[stop_time],
        frequencies=[
            parse.ScheduledTripFrequency(
                start_time=datetime.time(3, 4, 5),
                end_time=datetime.time(6, 7, 8),
                headway=30,
                frequency_based=False,
            )
        ],
    )

    schedule = parse.ScheduledService(
        id="schedule",
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=True,
        friday=True,
        saturday=True,
        sunday=True,
        trips=[trip],
        added_dates=[datetime.date(2016, 9, 10)],
        removed_dates=[datetime.date(2016, 9, 11), datetime.date(2016, 9, 12)],
    )

    actual_counts = importdriver.run_import(
        previous_update.pk, ParserForTesting([schedule])
    )

    assert 1 == len(db_session.query(models.ScheduledService).all())
    assert 1 == len(db_session.query(models.ScheduledServiceAddition).all())
    assert 2 == len(db_session.query(models.ScheduledServiceRemoval).all())
    assert 1 == len(db_session.query(models.ScheduledTrip).all())
    assert 1 == len(db_session.query(models.ScheduledTripFrequency).all())
    assert 1 == len(db_session.query(models.ScheduledTripStopTime).all())
    assert (1, 0, 0) == actual_counts

    # Just to make sure we can delete it all
    importdriver.run_import(current_update.pk, ParserForTesting([]))


def test_direction_rules__skip_unknown_stop(
    db_session, system_1, current_update,
):
    current = [
        parse.DirectionRule(name="Rule", id="blah", track="new track", stop_id="104401")
    ]

    actual_counts = importdriver.run_import(
        current_update.pk, ParserForTesting(current)
    )

    assert [] == db_session.query(models.DirectionRule).all()
    assert (0, 0, 0) == actual_counts


def test_unknown_type(current_update):
    with pytest.raises(TypeError):
        importdriver.run_import(current_update.pk, ParserForTesting(["string"]))


def test_flush(db_session, add_model, system_1, previous_update, current_update):
    current_update.update_type = models.FeedUpdate.Type.FLUSH

    add_model(
        models.Stop(
            system=system_1,
            source_pk=previous_update.pk,
            type=models.Stop.Type.STATION,
        )
    )
    add_model(models.Route(system=system_1, source_pk=previous_update.pk,))

    importdriver.run_import(current_update.pk, ParserForTesting([]))

    assert [] == db_session.query(models.Route).all()


def test_trip__route_from_schedule(
    db_session, add_model, system_1, route_1_1, current_update, feed_1_1_update_1
):
    add_model(
        models.ScheduledTrip(
            id="trip",
            route=route_1_1,
            service=add_model(
                models.ScheduledService(
                    id="service", system=system_1, source=feed_1_1_update_1
                )
            ),
        )
    )

    new_trip = parse.Trip(id="trip", route_id=None, direction_id=True)

    importdriver.run_import(current_update.pk, ParserForTesting([new_trip]))

    all_trips = db_session.query(models.Trip).all()

    assert 1 == len(all_trips)
    assert "trip" == all_trips[0].id
    assert route_1_1 == all_trips[0].route


def test_trip__invalid_route(db_session, system_1, route_1_1, current_update):
    new_trip = parse.Trip(id="trip", route_id="unknown_route", direction_id=True)

    importdriver.run_import(current_update.pk, ParserForTesting([new_trip]))

    all_trips = db_session.query(models.Trip).all()

    assert [] == all_trips


def test_trip__invalid_stops_in_stop_times(
    db_session, system_1, route_1_1, stop_1_1, current_update
):
    new_trip = parse.Trip(
        id="trip",
        route_id=route_1_1.id,
        direction_id=True,
        stop_times=[
            parse.TripStopTime(stop_id=stop_1_1.id, stop_sequence=2),
            parse.TripStopTime(stop_id=stop_1_1.id + "blah_bla", stop_sequence=3),
        ],
    )

    importdriver.run_import(current_update.pk, ParserForTesting([new_trip]))

    all_trips = db_session.query(models.Trip).all()

    assert 1 == len(all_trips)
    assert 1 == len(all_trips[0].stop_times)


TIME_1 = datetime.datetime.fromtimestamp(1000100, tz=pytz.timezone("UTC"))
TIME_2 = datetime.datetime.fromtimestamp(1000200, tz=pytz.timezone("UTC"))
TIME_3 = datetime.datetime.fromtimestamp(1000300, tz=pytz.timezone("UTC"))
STOP_ID_1 = "stop_id_1"
STOP_ID_2 = "stop_id_2"
STOP_ID_3 = "stop_id_3"


@dataclasses.dataclass
class TripStopTimeWithFuture(parse.TripStopTime):
    future: bool = True


# Just to make the parameters in the next test easier to follow
def trip_stop_time(stop_sequence, stop_id, arrival_time, future=None):
    if future is None:
        return parse.TripStopTime(
            stop_sequence=stop_sequence, stop_id=stop_id, arrival_time=arrival_time,
        )
    return TripStopTimeWithFuture(
        stop_sequence=stop_sequence,
        stop_id=stop_id,
        arrival_time=arrival_time,
        future=future,
    )


@pytest.mark.parametrize(
    "old_stop_time_data,new_stop_time_data,expected_stop_time_data",
    [
        [  # Basic arrival time update case
            [
                trip_stop_time(1, STOP_ID_1, TIME_1),
                trip_stop_time(2, STOP_ID_2, TIME_2),
            ],
            [trip_stop_time(2, STOP_ID_2, TIME_3)],
            [
                trip_stop_time(1, STOP_ID_1, TIME_1, False),
                trip_stop_time(2, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Converting a null stop sequence to a correct one based on the DB
            [
                trip_stop_time(1, STOP_ID_1, TIME_1),
                trip_stop_time(4, STOP_ID_2, TIME_2),
            ],
            [trip_stop_time(None, STOP_ID_2, TIME_3)],
            [
                trip_stop_time(1, STOP_ID_1, TIME_1, False),
                trip_stop_time(4, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Converting a null stop sequence to a correct one multiple times
            [
                trip_stop_time(None, STOP_ID_1, TIME_1),
                trip_stop_time(None, STOP_ID_2, TIME_2),
            ],
            [trip_stop_time(None, STOP_ID_2, TIME_3)],
            [
                trip_stop_time(1, STOP_ID_1, TIME_1, False),
                trip_stop_time(2, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Converting a null stop sequence to a correct one with change of schedule
            [
                trip_stop_time(None, STOP_ID_1, TIME_1),
                trip_stop_time(None, STOP_ID_2, TIME_2),
                trip_stop_time(None, STOP_ID_3, TIME_3),
            ],
            [
                trip_stop_time(None, STOP_ID_3, TIME_2),
                trip_stop_time(None, STOP_ID_2, TIME_3),
            ],
            [
                trip_stop_time(1, STOP_ID_1, TIME_1, False),
                trip_stop_time(3, STOP_ID_3, TIME_2, True),
                trip_stop_time(4, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Converting a null stop sequence to a correct one with change of schedule 2
            [
                trip_stop_time(None, STOP_ID_1, TIME_1),
                trip_stop_time(None, STOP_ID_2, TIME_2),
                trip_stop_time(None, STOP_ID_3, TIME_3),
            ],
            [
                trip_stop_time(None, STOP_ID_1, TIME_1),
                trip_stop_time(None, STOP_ID_3, TIME_3),
            ],
            [
                trip_stop_time(1, STOP_ID_1, TIME_1, True),
                trip_stop_time(3, STOP_ID_3, TIME_3, True),
            ],
        ],
        [  # Deleting an extra stop time if it disappears
            [
                trip_stop_time(None, STOP_ID_1, TIME_1),
                trip_stop_time(None, STOP_ID_2, TIME_2),
            ],
            [trip_stop_time(None, STOP_ID_1, TIME_1)],
            [trip_stop_time(1, STOP_ID_1, TIME_1, True)],
        ],
        [  # Setting the stop sequences of a new trip
            [],
            [
                trip_stop_time(None, STOP_ID_1, TIME_1),
                trip_stop_time(None, STOP_ID_2, TIME_3),
            ],
            [
                trip_stop_time(1, STOP_ID_1, TIME_1, True),
                trip_stop_time(2, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Handling malformed stop sequences in a new trip
            [],
            [
                trip_stop_time(4, STOP_ID_1, TIME_1),
                trip_stop_time(2, STOP_ID_2, TIME_3),
            ],
            [
                trip_stop_time(4, STOP_ID_1, TIME_1, True),
                trip_stop_time(5, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Handling a shift in the stop sequences in an existing trip
            [
                trip_stop_time(3, STOP_ID_1, TIME_1),
                trip_stop_time(6, STOP_ID_2, TIME_3),
            ],
            [trip_stop_time(5, STOP_ID_2, TIME_3)],
            [
                trip_stop_time(3, STOP_ID_1, TIME_1, False),
                trip_stop_time(5, STOP_ID_2, TIME_3, True),
            ],
        ],
        [  # Ensuring a lower stop sequence overwrites existing data
            [
                trip_stop_time(1, STOP_ID_1, TIME_1),
                trip_stop_time(2, STOP_ID_2, TIME_2),
            ],
            [trip_stop_time(1, STOP_ID_2, TIME_3)],
            [trip_stop_time(1, STOP_ID_2, TIME_3, True)],
        ],
        [  # Ensuring stop sequences are shifted forward
            [
                trip_stop_time(1, STOP_ID_1, TIME_1),
                trip_stop_time(2, STOP_ID_2, TIME_2),
            ],
            [
                trip_stop_time(5, STOP_ID_1, TIME_1),
                trip_stop_time(6, STOP_ID_2, TIME_2),
            ],
            [
                trip_stop_time(5, STOP_ID_1, TIME_1, True),
                trip_stop_time(6, STOP_ID_2, TIME_2, True),
            ],
        ],
    ],
)
def test_trip__stop_time_reconciliation(
    db_session,
    add_model,
    system_1,
    route_1_1,
    previous_update,
    current_update,
    old_stop_time_data,
    new_stop_time_data,
    expected_stop_time_data,
    feed_1_1_update_1,
):
    stop_pk_to_stop = {}
    all_stop_ids = set(
        trip_stop_time.stop_id
        for trip_stop_time in itertools.chain(old_stop_time_data, new_stop_time_data)
    )
    for stop_id in all_stop_ids:
        stop = add_model(
            models.Stop(
                id=stop_id,
                system=system_1,
                type=models.Stop.Type.STATION,
                source=feed_1_1_update_1,
            )
        )
        stop_pk_to_stop[stop.pk] = stop

    trip = parse.Trip(
        id="trip",
        route_id=route_1_1.id,
        direction_id=True,
        stop_times=old_stop_time_data,
    )

    importdriver.run_import(previous_update.pk, ParserForTesting([trip]))

    trip.stop_times = new_stop_time_data

    importdriver.run_import(current_update.pk, ParserForTesting([trip]))

    actual_stop_times = [
        convert_trip_stop_time_model_to_parse(trip_stop_time, stop_pk_to_stop)
        for trip_stop_time in db_session.query(models.Trip).all()[0].stop_times
    ]

    assert expected_stop_time_data == actual_stop_times


@pytest.mark.parametrize(
    "entity",
    [
        parse.Route(id="my_special_route_id", type=parse.Route.Type.RAIL),
        parse.Stop(
            id="my_special_stop_id",
            name="station",
            type=parse.Stop.Type.STATION,
            latitude=0,
            longitude=0,
        ),
        parse.Trip(
            id="my_special_trip_id", route_id=route_data.ROUTE_1_1_ID, direction_id=True
        ),
        parse.Alert(id="my_special_alert_id"),
        parse.DirectionRule(id="my_special_direction_id", name="uptown"),
        parse.ScheduledService.create_empty("my_special_service_id"),
    ],
)
def test_move_entity_across_feeds(current_update, other_feed_update, route_1_1, entity):
    importdriver.run_import(other_feed_update.pk, ParserForTesting([entity]))

    importdriver.run_import(current_update.pk, ParserForTesting([entity]))


def convert_trip_stop_time_model_to_parse(
    trip_stop_time: models.TripStopTime, stop_pk_to_stop
):
    return TripStopTimeWithFuture(
        stop_sequence=trip_stop_time.stop_sequence,
        future=trip_stop_time.future,
        arrival_time=trip_stop_time.arrival_time,
        stop_id=stop_pk_to_stop[trip_stop_time.stop_pk].id,
    )


def test_entities_skipped(db_session, current_update):
    class BuggyParser(parse.parser.CallableBasedParser):
        @property
        def supported_types(self):
            return {parse.Stop}

    parser = BuggyParser(lambda: [new_route])

    result = importdriver.run_import(current_update.pk, parser)

    assert [] == db_session.query(models.Route).all()
    assert (0, 0, 0) == result


def test_parse_error(current_update):
    class BuggyParser(parse.TransiterParser):
        def get_routes(self):
            raise ValueError

    with pytest.raises(ValueError):
        importdriver.run_import(current_update.pk, BuggyParser())


@pytest.mark.parametrize("entity_type", ["routes", "stops", "trips", "agencies"])
@pytest.mark.parametrize("valid_id", [True, False])
def test_alert__route_linking(
    db_session,
    current_update,
    route_1_1,
    stop_1_1,
    trip_1,
    agency_1_1,
    entity_type,
    valid_id,
):
    alert_kwargs = {}
    entity = None
    if entity_type == "routes":
        alert_kwargs["route_ids"] = [route_1_1.id if valid_id else "buggy_route_id"]
        entity = route_1_1
    elif entity_type == "stops":
        alert_kwargs["stop_ids"] = [stop_1_1.id if valid_id else "buggy_stop_id"]
        entity = stop_1_1
    elif entity_type == "trips":
        alert_kwargs["trip_ids"] = [trip_1.id if valid_id else "buggy_trip_id"]
        entity = trip_1
    elif entity_type == "agencies":
        alert_kwargs["agency_ids"] = [agency_1_1.id if valid_id else "buggy_agency_id"]
        entity = agency_1_1

    alert = parse.Alert(id="alert", **alert_kwargs)

    importdriver.run_import(current_update.pk, ParserForTesting([alert]))

    persisted_alert = db_session.query(models.Alert).all()[0]

    if valid_id:
        assert getattr(persisted_alert, entity_type) == [entity]
    else:
        assert getattr(persisted_alert, entity_type) == []


@pytest.fixture
def trip_for_vehicle(
    add_model, system_1, route_1_1, stop_1_1, stop_1_2, stop_1_3, feed_1_1_update_1
):
    return add_model(
        models.Trip(
            id="trip_id",
            route=route_1_1,
            current_stop_sequence=2,
            stop_times=[
                models.TripStopTime(stop_sequence=1, stop=stop_1_1),
                models.TripStopTime(stop_sequence=2, stop=stop_1_2),
                models.TripStopTime(stop_sequence=3, stop=stop_1_3),
            ],
            source=feed_1_1_update_1,
        )
    )


@pytest.mark.parametrize("provide_stop_id", [True, False])
@pytest.mark.parametrize("provide_stop_sequence", [True, False])
def test_vehicle__set_stop_simple_case(
    db_session,
    current_update,
    trip_for_vehicle,
    stop_1_3,
    provide_stop_id,
    provide_stop_sequence,
):
    vehicle = parse.Vehicle(
        id="vehicle_id",
        trip_id="trip_id",
        current_stop_id=stop_1_3.id if provide_stop_id else None,
        current_stop_sequence=3 if provide_stop_sequence else None,
    )

    importdriver.run_import(current_update.pk, ParserForTesting([vehicle]))

    persisted_vehicle = db_session.query(models.Vehicle).all()[0]

    if not provide_stop_id and not provide_stop_sequence:
        assert persisted_vehicle.current_stop is None
        assert persisted_vehicle.current_stop_sequence is None
    else:
        assert persisted_vehicle.current_stop == stop_1_3
        assert persisted_vehicle.current_stop_sequence == 3


@pytest.mark.parametrize("vehicle_id", [None, "vehicle_id"])
def test_vehicle__no_vehicle_id(
    db_session, current_update, trip_for_vehicle, stop_1_3, vehicle_id,
):
    vehicle = parse.Vehicle(id=vehicle_id, trip_id="trip_id")

    importdriver.run_import(current_update.pk, ParserForTesting([vehicle]))

    persisted_vehicle = db_session.query(models.Vehicle).all()[0]

    db_session.refresh(trip_for_vehicle)

    assert trip_for_vehicle.vehicle == persisted_vehicle
    assert persisted_vehicle.trip == trip_for_vehicle


def test_vehicle__duplicate_trip_ids(
    db_session, current_update, trip_for_vehicle, stop_1_3,
):
    vehicle = parse.Vehicle(id=None, trip_id="trip_id")

    result = importdriver.run_import(
        current_update.pk, ParserForTesting([vehicle, vehicle])
    )

    assert (1, 0, 0) == result


def test_vehicle__merged_vehicle_edge_case(
    db_session, previous_update, current_update, trip_for_vehicle, stop_1_3,
):
    vehicle_1 = parse.Vehicle(id=None, trip_id="trip_id")
    vehicle_2 = parse.Vehicle(id="vehicle_id", trip_id=None)
    vehicle_3 = parse.Vehicle(id="vehicle_id", trip_id="trip_id")

    importdriver.run_import(
        previous_update.pk, ParserForTesting([vehicle_1, vehicle_2])
    )
    db_session.refresh(trip_for_vehicle)

    result = importdriver.run_import(current_update.pk, ParserForTesting([vehicle_3]))

    assert (0, 0, 2) == result


def test_vehicle__delete_with_trip_attached(
    db_session,
    add_model,
    system_1,
    previous_update,
    current_update,
    trip_for_vehicle,
    stop_1_3,
):
    add_model(
        models.Vehicle(
            id="vehicle_id",
            system=system_1,
            source=previous_update,
            trip=trip_for_vehicle,
        )
    )

    importdriver.run_import(current_update.pk, ParserForTesting([]))

    db_session.refresh(trip_for_vehicle)

    assert trip_for_vehicle.vehicle is None


def test_vehicle__move_between_trips_attached(
    db_session,
    add_model,
    system_1,
    route_1_1,
    previous_update,
    current_update,
    trip_for_vehicle,
    stop_1_3,
):
    vehicle = add_model(
        models.Vehicle(
            id="vehicle_id",
            system=system_1,
            source=previous_update,
            trip=trip_for_vehicle,
        )
    )

    importdriver.run_import(
        current_update.pk,
        ParserForTesting(
            [
                parse.Trip(id="trip_id_2", route_id=route_1_1.id),
                parse.Vehicle(id="vehicle_id", trip_id="trip_id_2"),
            ]
        ),
    )

    db_session.refresh(trip_for_vehicle)
    new_trip = (
        db_session.query(models.Trip)
        .filter(models.Trip.id == "trip_id_2")
        .one_or_none()
    )

    assert trip_for_vehicle.vehicle is None
    assert new_trip.vehicle == vehicle


@pytest.mark.parametrize("previous_transfer,expected_deleted", [[True, 1], [False, 0]])
@pytest.mark.parametrize(
    "from_stop_valid,to_stop_valid,expected_added",
    [[True, True, 1], [False, True, 0], [True, False, 0], [False, False, 0]],
)
def test_transfers(
    previous_update,
    current_update,
    stop_1_1,
    stop_1_2,
    from_stop_valid,
    to_stop_valid,
    expected_added,
    previous_transfer,
    expected_deleted,
):
    transfer = parse.Transfer(
        from_stop_id=stop_1_1.id if from_stop_valid else "blah",
        to_stop_id=stop_1_2.id if to_stop_valid else "blaf",
        min_transfer_time=300,
    )

    if previous_transfer:
        importdriver.run_import(
            previous_update.pk,
            ParserForTesting(
                [parse.Transfer(from_stop_id=stop_1_1.id, to_stop_id=stop_1_2.id)]
            ),
        )

    result = importdriver.run_import(current_update.pk, ParserForTesting([transfer]))

    assert (expected_added, 0, expected_deleted) == result
