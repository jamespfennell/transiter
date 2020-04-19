import pytest

from transiter import models
from transiter.services.update import sync


# TODO
#  stop graph linking tests
#  route and stop feed stealing?
#  direction rules no feed stealing?
#  trip:
#  - add with route coming from schedule
#  - add with invalid route
#  - add with invalid stops in stop times
#  - add with pre-existing data, make past stops, make new stops
#  - regular add new trip
#  - delete trip
#  - scheduler - basic add, update, delete


@pytest.fixture
def feed(add_model, system_1):
    return add_model(models.Feed(system=system_1, id="feed", auto_update_enabled=False))


@pytest.fixture
def previous_update(add_model, feed):
    return add_model(models.FeedUpdate(feed=feed))


@pytest.fixture
def current_update(add_model, feed):
    return add_model(models.FeedUpdate(feed=feed))


@pytest.mark.parametrize(
    "entity_type,previous,current,expected_counts",
    [
        [
            models.Route,
            [],
            [models.Route(id="route", description="new route")],
            (1, 0, 0),
        ],
        [
            models.Route,
            [models.Route(id="route", description="old route")],
            [models.Route(id="route", description="new route")],
            (0, 1, 0),
        ],
        [
            models.Route,
            [models.Route(id="route", description="old route")],
            [],
            (0, 0, 1),
        ],
        [models.Stop, [], [models.Stop(id="route", name="new stop")], (1, 0, 0)],
        [
            models.Stop,
            [models.Stop(id="route", name="old stop")],
            [models.Stop(id="route", name="new stop")],
            (0, 1, 0),
        ],
        [models.Stop, [models.Stop(id="route", name="old stop")], [], (0, 0, 1)],
    ],
)
def test_sync__simple_create_update_delete(
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
        entity.system = system_1
        entity.source = previous_update
        add_model(entity)

    actual_counts = sync.sync(current_update.pk, current)

    def fields_to_compare(entity):
        if entity_type is models.Route:
            return entity.id, entity.description, entity.source_pk
        if entity_type is models.Stop:
            return entity.id, entity.name, entity.source_pk
        raise NotImplementedError

    assert set(map(fields_to_compare, current)) == set(
        map(fields_to_compare, db_session.query(entity_type).all())
    )
    assert expected_counts == actual_counts


@pytest.mark.parametrize(
    "previous,current,expected_counts",
    [
        [[], [models.DirectionRule(id="route", track="new track")], (1, 0, 0)],
        [
            [models.DirectionRule(id="route", track="old track")],
            [models.DirectionRule(id="route", track="new track")],
            (0, 1, 0),
        ],
        [[models.DirectionRule(id="route", track="old track")], [], (0, 0, 1)],
    ],
)
def test_direction_rules(
    db_session,
    add_model,
    system_1,
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

    actual_counts = sync.sync(current_update.pk, current)

    def fields_to_compare(entity):
        return entity.stop_pk, entity.track, entity.source_pk

    assert set(map(fields_to_compare, expected_entities)) == set(
        map(fields_to_compare, db_session.query(models.DirectionRule).all())
    )
    assert expected_counts == actual_counts


def test_schedule(db_session, stop_1_1, route_1_1, previous_update, current_update):
    stop_time = models.ScheduledTripStopTimeLight()
    stop_time.stop_id = stop_1_1.id
    stop_time.stop_sequence = 3

    trip = models.ScheduledTrip(id="trid_id")
    trip.route_id = route_1_1.id
    trip.stop_times_light = []
    trip.stop_times_light.append(stop_time)

    schedule = models.ScheduledService(id="schedule")
    schedule.trips = []
    schedule.trips.append(trip)

    actual_counts = sync.sync(current_update.pk, [schedule])

    assert 1 == len(db_session.query(models.ScheduledService).all())
    assert 1 == len(db_session.query(models.ScheduledTrip).all())
    assert 1 == len(db_session.query(models.ScheduledTripStopTime).all())
    assert (1, 0, 0) == actual_counts


def test_direction_rules__skip_unknown_stop(
    db_session, system_1, current_update,
):
    current = [models.DirectionRule(id="blah", track="new track", stop_pk=104401)]

    actual_counts = sync.sync(current_update.pk, current)

    assert [] == db_session.query(models.DirectionRule).all()
    assert (0, 0, 0) == actual_counts


def test_unknown_type(current_update):
    with pytest.raises(TypeError):
        sync.sync(current_update.pk, ["string"])


def test_flush(db_session, add_model, system_1, previous_update, current_update):
    current_update.update_type = models.FeedUpdate.Type.FLUSH

    add_model(models.Stop(system=system_1, source_pk=previous_update.pk))
    add_model(models.Route(system=system_1, source_pk=previous_update.pk))

    sync.sync(current_update.pk, [])

    assert [] == db_session.query(models.Route).all()
