import csv
import dataclasses
import io
import typing
import zipfile

import pytest
import requests

SYSTEM_CONFIG = """

name: Test System for transfers

feeds:

  gtfsstatic:
    http:
      url: "{static_feed_url}"
    parser:
      built_in: GTFS_STATIC
    required_for_install: true

"""


@pytest.fixture
def transfer_systems(
    install_system, source_server, source_server_host_within_transiter, system_id
):
    def build_zip(stops: typing.List[Stop]):
        stops_file = io.StringIO()
        writer = csv.writer(stops_file)
        writer.writerow(["stop_id", "stop_name", "stop_lat", "stop_lon"])
        for stop in stops:
            writer.writerow([stop.id, stop.id, stop.latitude, stop.longitude])

        output_bytes = io.BytesIO()
        with zipfile.ZipFile(output_bytes, "w") as zip_file:
            zip_file.writestr("stops.txt", stops_file.getvalue())
        return output_bytes.getvalue()

    def install(system_id_, stops):
        static_feed_url = source_server.create(
            "", "/" + system_id_ + "/gtfs-static.zip"
        )
        source_server.put(static_feed_url, build_zip(stops))

        install_system(
            system_id_,
            SYSTEM_CONFIG.format(
                static_feed_url=source_server_host_within_transiter
                + "/"
                + static_feed_url
            ),
        )

    system_1_id = system_id + "_1"
    system_2_id = system_id + "_2"
    install(system_1_id, STOPS_1)
    install(system_2_id, STOPS_2)
    return system_1_id, system_2_id


@dataclasses.dataclass
class Stop:
    id: str
    latitude: float
    longitude: float


STOP_1_1 = "1_1"
STOP_1_2 = "1_2"
STOP_1_3 = "1_3"
STOP_2_1 = "2_1"
STOP_2_2 = "2_2"
STOP_2_3 = "2_3"
STOPS_1 = [Stop(STOP_1_1, 1.0, 1), Stop(STOP_1_2, 2.0, 2), Stop(STOP_1_3, 4.0, 4)]
STOPS_2 = [Stop(STOP_2_1, 1.4, 1), Stop(STOP_2_2, 2.8, 2), Stop(STOP_2_3, 5.2, 4)]

PARAMETERS = [
    [300, set()],
    [50000, {(STOP_1_1, STOP_2_1), (STOP_2_1, STOP_1_1)}],
    [
        100000,
        {
            (STOP_1_1, STOP_2_1),
            (STOP_2_1, STOP_1_1),
            (STOP_1_2, STOP_2_2),
            (STOP_2_2, STOP_1_2),
        },
    ],
]


@pytest.mark.parametrize("distance,expected_tuples", PARAMETERS)
class TestTransfers:
    def test_preview(self, transfer_systems, transiter_host, distance, expected_tuples):
        system_1_id, system_2_id = transfer_systems

        preview_response = requests.post(
            transiter_host + "/admin/transfers-config/preview",
            params={"system_id": [system_1_id, system_2_id], "distance": distance},
        ).json()

        transfer_tuples = {
            (transfer["from_stop"]["id"], transfer["to_stop"]["id"])
            for transfer in preview_response
        }

        assert expected_tuples == transfer_tuples

    def test_create(self, transfer_systems, transiter_host, distance, expected_tuples):
        system_1_id, system_2_id = transfer_systems

        create_response = requests.post(
            transiter_host + "/admin/transfers-config",
            params={"system_id": [system_1_id, system_2_id], "distance": distance},
        ).json()
        config_id = create_response["id"]

        # Verify visible in the list endpoint
        get_response = requests.get(transiter_host + "/admin/transfers-config").json()
        all_config_ids = [config["id"] for config in get_response]
        assert config_id in all_config_ids

        # Verify visible in the get endpoint
        assert expected_tuples == calculate_transfer_tuples_from_config(
            transiter_host, config_id,
        )

        # Verify transfers were actually created.
        assert expected_tuples == calculate_transfer_tuples_from_stops(
            transiter_host, system_1_id, system_2_id
        )

    def test_delete(self, transfer_systems, transiter_host, distance, expected_tuples):
        system_1_id, system_2_id = transfer_systems

        create_response = requests.post(
            transiter_host + "/admin/transfers-config",
            params={"system_id": [system_1_id, system_2_id], "distance": distance},
        ).json()
        config_id = create_response["id"]

        delete_response = requests.delete(
            transiter_host + "/admin/transfers-config/" + config_id,
        )
        delete_response.raise_for_status()

        # Verify removed from the list endpoint
        get_response = requests.get(transiter_host + "/admin/transfers-config").json()
        all_config_ids = [config["id"] for config in get_response]
        assert config_id not in all_config_ids

        # Verify removed from the get endpoint
        get_response = requests.get(
            transiter_host + "/admin/transfers-config/" + config_id,
        )
        assert get_response.status_code == 404

        # Verify transfers were removed.
        assert set() == calculate_transfer_tuples_from_stops(
            transiter_host, system_1_id, system_2_id
        )


@pytest.mark.parametrize("initial_distance,initial_tuples", PARAMETERS)
@pytest.mark.parametrize("updated_distance,updated_tuples", PARAMETERS)
def test_update_distance(
    transfer_systems,
    transiter_host,
    initial_distance,
    initial_tuples,
    updated_distance,
    updated_tuples,
):
    system_1_id, system_2_id = transfer_systems

    create_response = requests.post(
        transiter_host + "/admin/transfers-config",
        params={"system_id": [system_1_id, system_2_id], "distance": initial_distance},
    ).json()
    config_id = create_response["id"]

    updated_response = requests.put(
        f"{transiter_host}/admin/transfers-config/{config_id}",
        params={"system_id": [system_1_id, system_2_id], "distance": updated_distance},
    )
    updated_response.raise_for_status()

    assert updated_tuples == calculate_transfer_tuples_from_config(
        transiter_host, config_id
    )

    assert updated_tuples == calculate_transfer_tuples_from_stops(
        transiter_host, system_1_id, system_2_id
    )


def test_update_systems(transiter_host, system_id, transfer_systems, install_system_1):
    system_1_id, system_2_id = transfer_systems
    system_3_id = system_id + "_3"
    install_system_1(system_3_id)

    create_response = requests.post(
        transiter_host + "/admin/transfers-config",
        params={"system_id": [system_1_id, system_2_id], "distance": 5000000},
    ).json()
    config_id = create_response["id"]

    update_response = requests.put(
        f"{transiter_host}/admin/transfers-config/{config_id}",
        params={"system_id": [system_1_id, system_3_id], "distance": 50000},
    ).json()

    transfer_tuples = calculate_transfer_tuples_from_config(transiter_host, config_id)

    for tuple_ in [
        (STOP_1_1, STOP_2_1),
        (STOP_2_1, STOP_1_1),
        (STOP_1_2, STOP_2_2),
        (STOP_2_2, STOP_1_2),
    ]:
        assert tuple_ not in transfer_tuples


def calculate_transfer_tuples_from_config(transiter_host, config_id):
    get_response = requests.get(
        transiter_host + "/admin/transfers-config/" + config_id,
    ).json()
    return {
        (transfer["from_stop"]["id"], transfer["to_stop"]["id"])
        for transfer in get_response["transfers"]
    }


def calculate_transfer_tuples_from_stops(transiter_host, system_1_id, system_2_id):
    tuples = set()
    for system_id, stop_id in [
        (system_1_id, STOP_1_1),
        (system_1_id, STOP_1_2),
        (system_1_id, STOP_1_3),
        (system_2_id, STOP_2_1),
        (system_2_id, STOP_2_2),
        (system_2_id, STOP_2_3),
    ]:
        stop_response = requests.get(
            f"{transiter_host}/systems/{system_id}/stops/{stop_id}"
        ).json()
        tuples.update(
            (stop_id, transfer["to_stop"]["id"])
            for transfer in stop_response["transfers"]
        )
    return tuples
