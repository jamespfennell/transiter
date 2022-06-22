import datetime
import time

import pytest
import requests
from google.transit import gtfs_realtime_pb2 as gtfs

ONE_DAY_IN_SECONDS = 60 * 60 * 24
TIME_1 = datetime.datetime.utcfromtimestamp(time.time() - ONE_DAY_IN_SECONDS)
TIME_2 = datetime.datetime.utcfromtimestamp(time.time() + ONE_DAY_IN_SECONDS)

ALERT_SMALL_JSON = [{"id": "alert_id", "cause": "STRIKE", "effect": "MODIFIED_SERVICE"}]

ALERT_LARGE_JSON = [
    dict(
        **ALERT_SMALL_JSON[0],
        **{
            "active_period": {
                "starts_at": int(TIME_1.timestamp()),
                "ends_at": int(TIME_2.timestamp()),
            },
            "messages": [
                {
                    "header": "Advertencia",
                    "description": "",
                    "url": None,
                    "language": "es",
                }
            ],
        }
    )
]


def setup_test(
    system_id, informed_entity, install_system_1, transiter_host, source_server
):

    __, realtime_feed_url = install_system_1(system_id)

    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=int(time.time())),
        entity=[
            gtfs.FeedEntity(
                id="trip_id",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id="trip_id", route_id="A")
                ),
            ),
            gtfs.FeedEntity(
                id="alert_id",
                alert=gtfs.Alert(
                    active_period=[
                        gtfs.TimeRange(
                            start=int(TIME_1.timestamp()),
                            end=int(TIME_2.timestamp()),
                        )
                    ],
                    header_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text="Advertencia", language="es"
                            )
                        ],
                    ),
                    informed_entity=[informed_entity],
                    cause=gtfs.Alert.Cause.STRIKE,
                    effect=gtfs.Alert.Effect.MODIFIED_SERVICE,
                ),
            ),
        ],
    )

    source_server.put(realtime_feed_url, message.SerializeToString())
    requests.post(
        "{}/systems/{}/feeds/GtfsRealtimeFeed?sync=true".format(
            transiter_host, system_id
        )
    )


@pytest.mark.parametrize(
    "alerts_detail,expected_json",
    [
        [None, None],
        ["none", None],
        ["cause_and_effect", ALERT_SMALL_JSON],
        ["messages", ALERT_LARGE_JSON],
    ],
)
@pytest.mark.parametrize(
    "path,entity_id,entity_selector,default_expected_json",
    [
        ["routes", "A", gtfs.EntitySelector(route_id="A"), ALERT_SMALL_JSON],
        ["routes/A", None, gtfs.EntitySelector(route_id="A"), ALERT_LARGE_JSON],
        ["stops", "1A", gtfs.EntitySelector(stop_id="1A"), None],
        ["stops/1A", None, gtfs.EntitySelector(stop_id="1A"), ALERT_SMALL_JSON],
        [
            "routes/A/trips",
            "trip_id",
            gtfs.EntitySelector(trip=gtfs.TripDescriptor(trip_id="trip_id")),
            ALERT_SMALL_JSON,
        ],
        [
            "routes/A/trips/trip_id",
            None,
            gtfs.EntitySelector(trip=gtfs.TripDescriptor(trip_id="trip_id")),
            ALERT_LARGE_JSON,
        ],
        ["stops/1A", None, gtfs.EntitySelector(stop_id="1A"), ALERT_SMALL_JSON],
        [
            "agencies",
            "transiter_transit_agency",
            gtfs.EntitySelector(agency_id="transiter_transit_agency"),
            ALERT_SMALL_JSON,
        ],
        [
            "agencies/transiter_transit_agency",
            None,
            gtfs.EntitySelector(agency_id="transiter_transit_agency"),
            ALERT_LARGE_JSON,
        ],
    ],
)
def test_alerts_list_entities(
    install_system_1,
    transiter_host,
    source_server,
    path,
    entity_id,
    entity_selector,
    default_expected_json,
    alerts_detail: str,
    expected_json,
):
    system_id = "test_alerts__get_entity_" + str(hash(path))
    setup_test(
        system_id=system_id,
        informed_entity=entity_selector,
        install_system_1=install_system_1,
        transiter_host=transiter_host,
        source_server=source_server,
    )

    url = "{}/systems/{}/{}".format(transiter_host, system_id, path)
    if alerts_detail is not None:
        url += "?alerts_detail=" + alerts_detail
    else:
        expected_json = default_expected_json

    actual_data = requests.get(url).json()
    print(actual_data)

    if entity_id is not None:
        actual_data = {response["id"]: response for response in actual_data}[entity_id]

    if expected_json is None:
        assert "alerts" not in actual_data
    else:
        assert expected_json == actual_data["alerts"]
