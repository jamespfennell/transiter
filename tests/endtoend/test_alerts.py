import time
import pytest
from . import gtfs_realtime_pb2 as gtfs
from . import shared
from . import client

ONE_DAY_IN_SECONDS = 60 * 60 * 24
TIMESTAMP_1 = int(time.time()) - ONE_DAY_IN_SECONDS
TIMESTAMP_2 = int(time.time()) + ONE_DAY_IN_SECONDS


ALERT = client.Alert(
    id="alert_id",
    cause="STRIKE",
    effect="MODIFIED_SERVICE",
    currentActivePeriod=client.AlertActivePeriod(
        startsAt=TIMESTAMP_1,
        endsAt=TIMESTAMP_2,
    ),
    allActivePeriods=[
        client.AlertActivePeriod(
            startsAt=TIMESTAMP_1,
            endsAt=TIMESTAMP_2,
        )
    ],
    header=[
        client.AlertText(
            text="Advertencia",
            language="es",
        )
    ],
    description=[
        client.AlertText(
            text="Description",
            language="en",
        )
    ],
    url=[
        client.AlertText(
            text="URL",
            language="en",
        )
    ],
)

ALERT_REFERENCE = client.AlertReference(
    id=ALERT.id,
    effect=ALERT.effect,
    cause=ALERT.cause,
)

AGENCY_ID = "AgencyID"
ROUTE_ID = "RouteID"
STOP_ID = "StopID"
GTFS_STATIC_TXTAR = f"""
-- agency.txt --
agency_id,agency_name,agency_url,agency_timezone
{AGENCY_ID},AgencyName,AgencyURL,AgencyTimezone
-- routes.txt --
route_id,route_type
{ROUTE_ID},3
-- stops.txt --
stop_id
{STOP_ID}
"""

TRIP_ID = "trip_id"


def test_list_alerts(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_list_alerts = transiter_client.list_alerts(system_id)
    assert got_list_alerts.alerts == [ALERT]


def test_get_alert(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_alert = transiter_client.get_alert(system_id, ALERT.id)
    assert got_alert == ALERT


def test_alert_appears_in_list_agencies(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_list_agencies = transiter_client.list_agencies(system_id)
    assert got_list_agencies.agencies[0].alerts == [ALERT_REFERENCE]


def test_alert_appears_in_get_agency(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_agency = transiter_client.get_agency(system_id, AGENCY_ID)
    assert got_agency.alerts == [ALERT_REFERENCE]


def test_alert_appears_in_list_route(
    system_for_alerts_test,
    system_id,
    transiter_client,
):
    _ = system_for_alerts_test
    got_list_routes = transiter_client.list_routes(system_id)
    assert got_list_routes.routes[0].alerts == [ALERT_REFERENCE]


def test_alert_appears_in_get_route(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_route = transiter_client.get_route(system_id, ROUTE_ID)
    assert got_route.alerts == [ALERT_REFERENCE]


def test_alert_appears_in_list_stop(
    system_for_alerts_test,
    system_id,
    transiter_client,
):
    _ = system_for_alerts_test
    got_list_stops = transiter_client.list_stops(system_id)
    assert got_list_stops.stops[0].alerts == [ALERT_REFERENCE]


def test_alert_appears_in_get_stop(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_stop = transiter_client.get_stop(system_id, STOP_ID)
    assert got_stop.alerts == [ALERT_REFERENCE]


def test_alert_appears_in_get_trip(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_trip = transiter_client.get_trip(system_id, ROUTE_ID, TRIP_ID)
    assert got_trip.alerts == [ALERT_REFERENCE]


def test_alert_appears_in_list_trip(
    system_for_alerts_test,
    system_id,
    transiter_client: client.TransiterClient,
):
    _ = system_for_alerts_test
    got_list_trips = transiter_client.list_trips(system_id, ROUTE_ID, TRIP_ID)
    assert got_list_trips.trips[0].alerts == [ALERT_REFERENCE]


@pytest.fixture
def system_for_alerts_test(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
    source_server: shared.SourceServerClient,
):
    __, realtime_feed_url = install_system(system_id, GTFS_STATIC_TXTAR)

    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=int(time.time())),
        entity=[
            gtfs.FeedEntity(
                id=TRIP_ID,
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID, route_id=ROUTE_ID),
                ),
            ),
            gtfs.FeedEntity(
                id="alert_id",
                alert=gtfs.Alert(
                    active_period=[
                        gtfs.TimeRange(
                            start=TIMESTAMP_1,
                            end=TIMESTAMP_2,
                        )
                    ],
                    header_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text="Advertencia", language="es"
                            )
                        ],
                    ),
                    description_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text="Description", language="en"
                            )
                        ],
                    ),
                    url=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(text="URL", language="en")
                        ],
                    ),
                    informed_entity=[
                        gtfs.EntitySelector(agency_id=AGENCY_ID),
                        gtfs.EntitySelector(route_id=ROUTE_ID),
                        gtfs.EntitySelector(stop_id=STOP_ID),
                        gtfs.EntitySelector(
                            trip=gtfs.TripDescriptor(trip_id=TRIP_ID)
                        ),
                    ],
                    cause=gtfs.Alert.Cause.STRIKE,
                    effect=gtfs.Alert.Effect.MODIFIED_SERVICE,
                ),
            ),
        ],
    )

    source_server.put(realtime_feed_url, message.SerializeToString())
    transiter_client.perform_feed_update(system_id, shared.GTFS_REALTIME_FEED_ID)
