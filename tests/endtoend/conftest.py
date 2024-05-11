import os
import time
import uuid
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


@pytest.fixture
def install_system(
    request,
    source_server: shared.SourceServerClient,
    source_server_host_within_transiter,
    transiter_client: client.TransiterClient,
):
    def install(
        system_id: str,
        gtfs_static_txtar,
        config: str = shared.DEFAULT_SYSTEM_CONFIG,
        realtime_update_period=3600000,
    ):
        static_feed_url = source_server.create("", "/" + system_id + "/gtfs-static.zip")
        gtfs_static_txtar = shared.GTFS_STATIC_DEFAULT_TXTAR + gtfs_static_txtar
        source_server.put(static_feed_url, txtar.to_zip(gtfs_static_txtar))
        realtime_feed_url = source_server.create(
            "", "/" + system_id + "/gtfs-realtime.gtfs"
        )

        system_config = config.format(
            system_name="Test System",
            static_feed_id=shared.GTFS_STATIC_FEED_ID,
            static_feed_url=f"{source_server_host_within_transiter}/{static_feed_url}",
            realtime_feed_id=shared.GTFS_REALTIME_FEED_ID,
            realtime_feed_url=f"{source_server_host_within_transiter}/{realtime_feed_url}",
            realtime_periodic_update_period=realtime_update_period,
        )

        transiter_client.install_system(system_id, system_config)

        def delete():
            transiter_client.delete_system(system_id)

        request.addfinalizer(delete)

        return static_feed_url, realtime_feed_url

    return install


@pytest.fixture
def system_id(request):
    return request.node.name + "__" + str(uuid.uuid4())
