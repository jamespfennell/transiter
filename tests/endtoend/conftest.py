import io
import os
import time
import uuid
import zipfile
import json
import pytest
import requests


class SourceServerClient:
    def __init__(self, base_url, add_finalizer):
        self._created_urls = []
        self._base_url = base_url
        self._add_finalizer = add_finalizer

    def create(self, prefix="", suffix=""):
        response = requests.post(self._base_url)
        response.raise_for_status()
        created_url = response.text + suffix
        self._add_finalizer(self._delete_factory(created_url))
        self._created_urls.append(created_url)
        return created_url

    def put(self, url, content):
        requests.put(self._base_url + "/" + url, data=content).raise_for_status()

    def delete(self, url):
        requests.delete(self._base_url + "/" + url).raise_for_status()

    def _delete_factory(self, url):
        full_url = self._base_url + "/" + url

        def delete():
            requests.delete(full_url)

        return delete


@pytest.fixture
def source_server(request):
    return SourceServerClient(
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
    source_server: SourceServerClient,
    transiter_host,
    source_server_host_within_transiter,
):
    def install(system_id, system_config, expected_status="ACTIVE"):
        def delete():
            requests.delete(
                transiter_host + "/systems/" + system_id + "?sync=true"
            )

        system_config_url = source_server.create(
            "", "/" + system_id + "/system-config.yaml.jinja"
        )

        source_server.put(system_config_url, system_config)

        response = requests.put(
            transiter_host + "/systems/" + system_id,
            json={
                "yaml_config": {
                    "url": source_server_host_within_transiter + "/" + system_config_url
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
            if response.json()["status"] == expected_status:
                break
            time.sleep(0.05)
        assert response.json()["status"] == expected_status

        request.addfinalizer(delete)

    return install


SYSTEM_1_CONFIG = """

name: Test System

feeds:

  - id: gtfsstatic
    url: "{static_feed_url}"
    parser: GTFS_STATIC
    requiredForInstall: true

  - id: GtfsRealtimeFeed
    url: "{realtime_feed_url}"
    parser: GTFS_REALTIME
    schedulingPolicy: PERIODIC
    updatePeriodS: {realtime_periodic_update_period}
    gtfsRealtimeOptions:
      onlyProcessFullEntities: {only_process_full_entities}

"""


@pytest.fixture
def install_system_1(
    source_server: SourceServerClient,
    transiter_host,
    source_server_host_within_transiter,
    install_system,
):
    def install(system_id, realtime_periodic_update_period="3600000", only_process_full_entities = "false"):
        static_feed_url = source_server.create("", "/" + system_id + "/gtfs-static.zip")
        source_server.put(static_feed_url, get_zip("gtfsstatic"))
        realtime_feed_url = source_server.create(
            "", "/" + system_id + "/gtfs-realtime.gtfs"
        )

        system_config = SYSTEM_1_CONFIG.format(
            static_feed_url=source_server_host_within_transiter + "/" + static_feed_url,
            realtime_feed_url=source_server_host_within_transiter
            + "/"
            + realtime_feed_url,
            realtime_periodic_update_period=realtime_periodic_update_period,
            only_process_full_entities=only_process_full_entities,
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
