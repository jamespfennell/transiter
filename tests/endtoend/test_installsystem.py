from . import shared
from . import client

FEED_IDS = {shared.GTFS_REALTIME_FEED_ID, shared.GTFS_STATIC_FEED_ID}

STATIC_FEED = client.Feed(
    id=shared.GTFS_STATIC_FEED_ID,
    lastSuccessfulUpdateMs=None,
    lastSkippedUpdateMs=None,
    lastFailedUpdateMs=None,
)
REALTIME_FEED = client.Feed(
    id=shared.GTFS_REALTIME_FEED_ID,
    lastSuccessfulUpdateMs=None,
    lastSkippedUpdateMs=None,
    lastFailedUpdateMs=None,
)


def test_get_system(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, shared.GTFS_STATIC_DEFAULT_TXTAR)

    got_system = transiter_client.get_system(system_id)
    assert got_system == client.System(
        id=system_id,
        name="Test System",
        status="ACTIVE",
        agencies=client.ChildResources(count=1, path=f"systems/{system_id}/agencies"),
        feeds=client.ChildResources(count=2, path=f"systems/{system_id}/feeds"),
        routes=client.ChildResources(count=0, path=f"systems/{system_id}/routes"),
        stops=client.ChildResources(count=0, path=f"systems/{system_id}/stops"),
        transfers=client.ChildResources(count=0, path=f"systems/{system_id}/transfers"),
    )


def test_list_feeds(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, shared.GTFS_STATIC_DEFAULT_TXTAR)

    got_list_feeds = transiter_client.list_feeds(system_id)
    # Clear least successful update time because it's non-deterministic
    for feed in got_list_feeds.feeds:
        feed.lastSuccessfulUpdateMs = None
    assert got_list_feeds.feeds == [
        REALTIME_FEED,
        STATIC_FEED,
    ]


def test_get_feeds(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, shared.GTFS_STATIC_DEFAULT_TXTAR)

    got_feed = transiter_client.get_feed(system_id, REALTIME_FEED.id)
    assert got_feed == REALTIME_FEED


def test_update_system(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, shared.GTFS_STATIC_DEFAULT_TXTAR)
    got_system = transiter_client.get_system(system_id)
    assert got_system.name == "Test System"

    config = """
    name: New Name

    feeds:
      - id: new_feed
        url: "https://www.example.com"
        parser: GTFS_STATIC
        requiredForInstall: false
    """

    install_system(system_id, shared.GTFS_STATIC_DEFAULT_TXTAR, config=config)

    got_system = transiter_client.get_system(system_id)
    assert got_system.name == "New Name"
    assert got_system.feeds == client.ChildResources(
        count=1, path=f"systems/{system_id}/feeds"
    )

    got_list_feeds = transiter_client.list_feeds(system_id)
    assert got_list_feeds.feeds == [
        client.Feed(
            id="new_feed",
            lastSuccessfulUpdateMs=None,
            lastSkippedUpdateMs=None,
            lastFailedUpdateMs=None,
        ),
    ]


def test_delete_system(
    system_id, install_system, transiter_client: client.TransiterClient
):
    install_system(system_id, shared.GTFS_STATIC_DEFAULT_TXTAR)
    transiter_client.delete_system(system_id)

    response = transiter_client.get(f"systems/{system_id}")
    assert response.status_code == 404
