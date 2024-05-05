import requests
from . import shared

FEED_IDS = {shared.GTFS_REALTIME_FEED_ID, shared.GTFS_STATIC_FEED_ID}


def test_install_system__basic_data(system_id, install_system_1, transiter_host):

    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "Test System"


def test_install_system__feeds(system_id, install_system_1, transiter_host):

    install_system_1(system_id)

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    feeds_count = system_response["feeds"]["count"]
    assert len(FEED_IDS) == int(feeds_count)

    feeds_response = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds"
    ).json()
    actual_feed_ids = set([feed["id"] for feed in feeds_response["feeds"]])
    assert FEED_IDS == actual_feed_ids


def _test_install_system__bad_config(system_id, install_system, transiter_host):
    install_system(
        system_id,
        "This is not a valid Transiter YAML config!",
        expected_status="INSTALL_FAILED",
    )

    for sub_entity in ["stops", "routes", "feeds"]:
        sub_entity_response = requests.get(
            transiter_host + "/systems/" + system_id + "/" + sub_entity
        )
        assert sub_entity_response.status_code == 404


SYSTEM_CONFIG = """
name: Test System

feeds:
  - id: feed_1
    url: {feed_url}
    parser: GTFS_STATIC
    requiredForInstall: false

"""


def _test_install_system__bad_update(system_id, install_system, transiter_host):
    install_system(
        system_id,
        SYSTEM_CONFIG.format(feed_url="non_url"),
        expected_status="INSTALL_FAILED",
    )

    for sub_entity in ["stops", "routes", "feeds"]:
        sub_entity_response = requests.get(
            transiter_host + "/systems/" + system_id + "/" + sub_entity
        )
        assert sub_entity_response.status_code == 404


def test_delete(system_id, install_system_1, transiter_host):
    install_system_1(system_id)

    response = requests.delete(transiter_host + "/systems/" + system_id)
    response.raise_for_status()

    response = requests.get(transiter_host + "/systems/" + system_id)
    assert response.status_code == 404


def test_update_system(system_id, install_system, transiter_host):
    config = """
    name: {}

    feeds:
      - id: feed_1
        requiredForInstall: false
        schedulingPolicy: PERIODIC
        updatePeriodS: {}
        url: transiter.dev
        parser: GTFS_STATIC
    """

    install_system(system_id, config.format("name1", 5))

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "name1"
    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    # TODO: renable
    # assert "5" == feed_data["updatePeriodS"]

    install_system(system_id, config.format("name2", 15))

    system_response = requests.get(transiter_host + "/systems/" + system_id).json()
    assert system_response["name"] == "name2"
    feed_data = requests.get(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"
    ).json()
    # TODO: renable
    # assert "15" == feed_data["updatePeriodS"]
