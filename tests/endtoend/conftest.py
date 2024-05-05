import io
import os
import time
import uuid
import zipfile
import pytest
import requests
from . import client
from . import txtar
from . import shared


@pytest.fixture
def source_server(request) -> shared.SourceServerClient:
    return shared.SourceServerClient(
        os.environ.get("SOURCE_SERVER_HOST", "http://localhost:8090"),
        request.addfinalizer,
    )


@pytest.fixture(scope="session")
def transiter_host():
    host = os.environ.get("TRANSITER_HOST", "http://localhost:8082")
    for __ in range(20):
        try:
            requests.get(host, timeout=1).json()
            return host
        except requests.RequestException:
            pass
        time.sleep(0.5)
    assert False, "Transiter instance is not at available at {}".format(host)


@pytest.fixture
def transiter_client(transiter_host):
    return client.TransiterClient(transiter_host)


@pytest.fixture
def source_server_host_within_transiter():
    return os.environ.get(
        "SOURCE_SERVER_HOST_WITHIN_TRANSITER",
        os.environ.get("SOURCE_SERVER_HOST", "http://localhost:8090"),
    )


def get_zip(directory):
    output_bytes = io.BytesIO()
    # writing files to a zipfile
    data_dir = os.path.join(os.path.dirname(__file__), "data", directory)
    with zipfile.ZipFile(output_bytes, "w") as zip_file:
        for file_name in os.listdir(data_dir):
            full_path = os.path.join(data_dir, file_name)
            zip_file.write(full_path, arcname=file_name)
    return output_bytes.getvalue()


@pytest.fixture
def install_system(
    request,
    transiter_host,
):
    def install(system_id, system_config, expected_status="ACTIVE"):
        def delete():
            requests.delete(transiter_host + "/systems/" + system_id + "?sync=true")

        response = requests.put(
            transiter_host + "/systems/" + system_id,
            json={
                "yaml_config": {
                    "content": system_config,
                },
            },
        )
        if expected_status == "ACTIVE":
            # Uncomment this line to debug system install failures
            # print(json.dumps(response.json(), indent=2))
            response.raise_for_status()
        for _ in range(100):
            response = requests.get(transiter_host + "/systems/" + system_id)
            response.raise_for_status()
            if response.json()["status"] not in {"INSTALLING", "UPDATING"}:
                break
            time.sleep(0.05)
        assert response.json()["status"] == expected_status

        request.addfinalizer(delete)

    return install


SYSTEM_1_CONFIG = """

name: Test System

feeds:

  - id: {static_feed_id}
    url: "{static_feed_url}"
    parser: GTFS_STATIC
    requiredForInstall: true

  - id: {realtime_feed_id}
    url: "{realtime_feed_url}"
    parser: GTFS_REALTIME
    schedulingPolicy: PERIODIC
    updatePeriodS: {realtime_periodic_update_period}

"""


@pytest.fixture
def install_system_1(
    source_server: shared.SourceServerClient,
    source_server_host_within_transiter,
    install_system,
):
    def install(system_id, realtime_periodic_update_period="3600000"):
        static_feed_url = source_server.create("", "/" + system_id + "/gtfs-static.zip")
        source_server.put(static_feed_url, get_zip("gtfsstatic"))
        realtime_feed_url = source_server.create(
            "", "/" + system_id + "/gtfs-realtime.gtfs"
        )

        system_config = SYSTEM_1_CONFIG.format(
            static_feed_id=shared.GTFS_STATIC_FEED_ID,
            static_feed_url=f"{source_server_host_within_transiter}/{static_feed_url}",
            realtime_feed_id=shared.GTFS_REALTIME_FEED_ID,
            realtime_feed_url=f"{source_server_host_within_transiter}/{realtime_feed_url}",
            realtime_periodic_update_period=realtime_periodic_update_period,
        )

        install_system(system_id, system_config)
        return static_feed_url, realtime_feed_url

    return install


@pytest.fixture
def install_system_using_txtar(
    source_server: shared.SourceServerClient,
    source_server_host_within_transiter,
    install_system,
):
    def install(system_id: str, gtfs_static_txtar: str):
        static_feed_url = source_server.create("", "/" + system_id + "/gtfs-static.zip")
        gtfs_static_txtar = shared.GTFS_STATIC_DEFAULT_TXTAR + gtfs_static_txtar
        source_server.put(static_feed_url, txtar.to_zip(gtfs_static_txtar))
        realtime_feed_url = source_server.create(
            "", "/" + system_id + "/gtfs-realtime.gtfs"
        )

        system_config = SYSTEM_1_CONFIG.format(
            static_feed_id=shared.GTFS_STATIC_FEED_ID,
            static_feed_url=f"{source_server_host_within_transiter}/{static_feed_url}",
            realtime_feed_id=shared.GTFS_REALTIME_FEED_ID,
            realtime_feed_url=f"{source_server_host_within_transiter}/{realtime_feed_url}",
            realtime_periodic_update_period="3600000",
        )

        install_system(system_id, system_config)
        return static_feed_url, realtime_feed_url

    return install


@pytest.fixture
def updated_gtfs_zip():
    return get_zip("gtfsstatic_updated")


@pytest.fixture
def system_id(request):
    return request.node.name + "__" + str(uuid.uuid4())
