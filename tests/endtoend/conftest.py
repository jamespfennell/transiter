import io
import os
import time
import uuid
import zipfile

import pytest
import requests


class SourceServerClient:
    def __init__(self, base_url, add_finalizer):
        self._created_urls = []
        self._base_url = base_url
        self._add_finalizer = add_finalizer

    def put(self, url, content):
        requests.put(self._base_url + "/" + url, data=content).raise_for_status()

    def create(self, prefix="", suffix=""):
        response = requests.post(
            self._base_url, params={"prefix": prefix, "suffix": suffix}
        )
        response.raise_for_status()
        created_url = response.text
        self._add_finalizer(self._delete_factory(created_url))
        self._created_urls.append(created_url)
        return created_url

    def _delete_factory(self, url):
        full_url = self._base_url + "/" + url

        def delete():
            requests.delete(full_url)

        return delete


@pytest.fixture
def source_server(request):
    return SourceServerClient(
        os.environ.get("SOURCE_SERVER_HOST", "http://localhost:5001"),
        request.addfinalizer,
    )


@pytest.fixture(scope="session")
def transiter_host():
    host = os.environ.get("TRANSITER_HOST", "http://localhost:8000")
    for __ in range(20):
        try:
            response = requests.get(host + "/admin/health", timeout=1).json()
            if response["up"]:
                return host
        except requests.RequestException:
            pass
        time.sleep(0.5)
    assert False, "Transiter instance is not at available at {}".format(host)


@pytest.fixture
def source_server_host_within_transiter():
    return os.environ.get(
        "SOURCE_SERVER_HOST_WITHIN_TRANSITER",
        os.environ.get("SOURCE_SERVER_HOST", "http://localhost:5001"),
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
    def install(system_id, system_config, sync=True, expected_status="ACTIVE"):
        def delete():
            requests.delete(transiter_host + "/systems/" + system_id + "?sync=true")

        delete()

        system_config_url = source_server.create(
            "", "/" + system_id + "/system-config.yaml.jinja"
        )

        source_server.put(system_config_url, system_config)

        response = requests.put(
            transiter_host + "/systems/" + system_id + "?sync=" + str(sync).lower(),
            data={
                "config_file": source_server_host_within_transiter
                + "/"
                + system_config_url
            },
        )
        if expected_status == "ACTIVE":
            response.raise_for_status()
        if not sync:
            for _ in range(20):
                response = requests.get(transiter_host + "/systems/" + system_id)
                response.raise_for_status()
                if response.json()["status"] == expected_status:
                    break
                time.sleep(0.6)
            assert response.json()["status"] == expected_status

        request.addfinalizer(delete)

    return install


SYSTEM_1_CONFIG = """

name: Test System

feeds:

  gtfsstatic:
    http:
      url: "{static_feed_url}"
    parser:
      built_in: GTFS_STATIC
    required_for_install: true
    auto_update:
      period: 1 day

  GtfsRealtimeFeed:
    http:
      url: "{realtime_feed_url}"
    parser:
      built_in: GTFS_REALTIME
    auto_update:
      period: "{realtime_auto_update_period}"

"""


@pytest.fixture
def install_system_1(
    source_server: SourceServerClient,
    transiter_host,
    source_server_host_within_transiter,
    install_system,
):
    def install(system_id, realtime_auto_update_period="1 day", sync=True):
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
            realtime_auto_update_period=realtime_auto_update_period,
        )

        install_system(system_id, system_config, sync=sync)
        return static_feed_url, realtime_feed_url

    return install


@pytest.fixture
def updated_gtfs_zip():
    return get_zip("gtfsstatic_updated")


@pytest.fixture
def system_id(request):
    return request.node.originalname + "__" + str(uuid.uuid4())
