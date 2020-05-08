import datetime
import itertools

import pytest
import pytz

from transiter import models, parse
from transiter.services.update import sync
from .data import route_data


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
new_alert = parse.Alert(id="alert", header="header", description="description")
new_route = parse.Route(id="route", type=parse.Route.Type.RAIL, description="new_route")
new_stop = parse.Stop(
    id="route", name="new stop", latitude=0, longitude=0, type=parse.Stop.Type.STATION
)


@pytest.mark.parametrize(
    "entity_type,previous,current,expected_counts",
    [
        [models.Alert, [], [new_alert], (1, 0, 0)],
        [
            models.Alert,
            [models.Alert(id="alert", header="old header", description="old route")],
            [new_alert],
            (0, 1, 0),
        ],
        [
            models.Alert,
            [models.Alert(id="alert", header="old header", description="old route")],
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
            [models.Stop(id="route", name="old stop")],
            [new_stop],
            (0, 1, 0),
        ],
        [models.Stop, [models.Stop(id="route", name="old stop")], [], (0, 0, 1)],
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

    actual_counts = sync.sync(current_update.pk, ParserForTesting(current))

    def fields_to_compare(entity):
        if entity_type is models.Route:
            return entity.id, entity.description, entity.source_pk
        if entity_type is models.Stop:
            return entity.id, entity.name, entity.source_pk
        if entity_type is models.Alert:
            return entity.id, entity.description, entity.header
        if entity_type is models.Agency:
            return entity.id, entity.name
        raise NotImplementedError

    assert set(map(fields_to_compare, current)) == set(
        map(fields_to_compare, db_session.query(entity_type).all())
    )
    assert expected_counts == actual_counts


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
                is_station=True,
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

    sync.sync(current_update.pk, ParserForTesting(list(stop_id_to_stop.values())))

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

    sync.sync(current_update.pk, ParserForTesting([route, agency]))

    persisted_route = db_session.query(models.Route).all()[0]

    assert persisted_route.agency is not None


def test_alert__route_linking(db_session, previous_update, current_update, route_1_1):
    alert = parse.Alert(
        id="alert", header="header", description="description", route_ids=[route_1_1.id]
    )

    sync.sync(current_update.pk, ParserForTesting([alert]))

    persisted_alert = db_session.query(models.Alert).all()[0]

    assert persisted_alert.routes == [route_1_1]


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

    actual_counts = sync.sync(current_update.pk, ParserForTesting(current))

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

    actual_counts = sync.sync(previous_update.pk, ParserForTesting([schedule]))

    assert 1 == len(db_session.query(models.ScheduledService).all())
    assert 1 == len(db_session.query(models.ScheduledServiceAddition).all())
    assert 2 == len(db_session.query(models.ScheduledServiceRemoval).all())
    assert 1 == len(db_session.query(models.ScheduledTrip).all())
    assert 1 == len(db_session.query(models.ScheduledTripFrequency).all())
    assert 1 == len(db_session.query(models.ScheduledTripStopTime).all())
    assert (1, 0, 0) == actual_counts

    # Just to make sure we can delete it all
    sync.sync(current_update.pk, ParserForTesting([]))


def test_direction_rules__skip_unknown_stop(
    db_session, system_1, current_update,
):
    current = [
        parse.DirectionRule(name="Rule", id="blah", track="new track", stop_id="104401")
    ]

    actual_counts = sync.sync(current_update.pk, ParserForTesting(current))

    assert [] == db_session.query(models.DirectionRule).all()
    assert (0, 0, 0) == actual_counts


def test_unknown_type(current_update):
    with pytest.raises(TypeError):
        sync.sync(current_update.pk, ParserForTesting(["string"]))


def test_flush(db_session, add_model, system_1, previous_update, current_update):
    current_update.update_type = models.FeedUpdate.Type.FLUSH

    add_model(models.Stop(system=system_1, source_pk=previous_update.pk))
    add_model(models.Route(system=system_1, source_pk=previous_update.pk))

    sync.sync(current_update.pk, ParserForTesting([]))

    assert [] == db_session.query(models.Route).all()


def test_trip__route_from_schedule(
    db_session, add_model, system_1, route_1_1, current_update
):
    add_model(
        models.ScheduledTrip(
            id="trip",
            route=route_1_1,
            service=add_model(models.ScheduledService(id="service", system=system_1)),
        )
    )

    new_trip = parse.Trip(id="trip", route_id=None, direction_id=True)

    sync.sync(current_update.pk, ParserForTesting([new_trip]))

    all_trips = db_session.query(models.Trip).all()

    assert 1 == len(all_trips)
    assert "trip" == all_trips[0].id
    assert route_1_1 == all_trips[0].route


def test_trip__invalid_route(db_session, system_1, route_1_1, current_update):
    new_trip = parse.Trip(id="trip", route_id="unknown_route", direction_id=True)

    sync.sync(current_update.pk, ParserForTesting([new_trip]))

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

    sync.sync(current_update.pk, ParserForTesting([new_trip]))

    all_trips = db_session.query(models.Trip).all()

    assert 1 == len(all_trips)
    assert 1 == len(all_trips[0].stop_times)


def test_trip__stop_time_reconciliation(
    db_session, add_model, system_1, route_1_1, previous_update, current_update
):

    old_stop_time_data = [
        parse.TripStopTime(
            stop_sequence=1,
            stop_id="stop_id_1",
            arrival_time=datetime.datetime.fromtimestamp(1000100),
            future=True,
        ),
        parse.TripStopTime(
            stop_sequence=2,
            stop_id="stop_id_2",
            arrival_time=datetime.datetime.fromtimestamp(1000200),
            future=True,
        ),
    ]
    new_stop_time_data = [
        parse.TripStopTime(
            stop_sequence=2,
            stop_id="stop_id_2",
            arrival_time=datetime.datetime.fromtimestamp(1000300),
            future=True,
        ),
    ]

    expected_stop_time_data = [
        parse.TripStopTime(
            stop_sequence=1,
            stop_id="stop_id_1",
            arrival_time=datetime.datetime.fromtimestamp(
                1000100, tz=pytz.timezone("UTC")
            ),
            future=False,
        ),
        parse.TripStopTime(
            stop_sequence=2,
            stop_id="stop_id_2",
            arrival_time=datetime.datetime.fromtimestamp(
                1000300, tz=pytz.timezone("UTC")
            ),
            future=True,
        ),
    ]

    stop_pk_to_stop = {}
    all_stop_ids = set(
        trip_stop_time.stop_id
        for trip_stop_time in itertools.chain(old_stop_time_data, new_stop_time_data)
    )
    for stop_id in all_stop_ids:
        stop = add_model(models.Stop(id=stop_id, system=system_1))
        stop_pk_to_stop[stop.pk] = stop

    trip = parse.Trip(
        id="trip",
        route_id=route_1_1.id,
        direction_id=True,
        stop_times=old_stop_time_data,
    )

    sync.sync(previous_update.pk, ParserForTesting([trip]))

    trip.stop_times = new_stop_time_data

    sync.sync(current_update.pk, ParserForTesting([trip]))

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
        parse.Alert(id="my_special_alert_id", header="header", description="desc"),
        parse.DirectionRule(id="my_special_direction_id", name="uptown"),
        parse.ScheduledService.create_empty("my_special_service_id"),
    ],
)
def test_move_entity_across_feeds(current_update, other_feed_update, route_1_1, entity):
    sync.sync(other_feed_update.pk, ParserForTesting([entity]))

    sync.sync(current_update.pk, ParserForTesting([entity]))


def convert_trip_stop_time_model_to_parse(
    trip_stop_time: models.TripStopTime, stop_pk_to_stop
):
    return parse.TripStopTime(
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

    result = sync.sync(current_update.pk, parser)

    assert [] == db_session.query(models.Route).all()
    assert (0, 0, 0) == result


def test_parse_error(current_update):
    class BuggyParser(parse.TransiterParser):
        def get_routes(self):
            raise ValueError

    with pytest.raises(ValueError):
        sync.sync(current_update.pk, BuggyParser())


def test_alert__buggy_route(db_session, current_update):
    alert = parse.Alert(
        id="my_alert",
        header="header",
        description="description",
        route_ids=["buggy_route_id"],
    )

    sync.sync(current_update.pk, ParserForTesting([alert]))

    persisted_alerts = db_session.query(models.Alert).all()

    assert 1 == len(persisted_alerts)
    assert [] == persisted_alerts[0].routes
