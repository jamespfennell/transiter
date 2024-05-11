from . import client
import pytest


STOP_1_ID = "stop-1-id"
STOP_2_ID = "stop-2-id"
STOP_3_ID = "stop-3-id"
STOP_4_ID = "stop-4-id"
STOP_5_ID = "stop-5-id"

GTFS_STATIC_TXTAR = f"""
-- stops.txt --
stop_id,parent_station
{STOP_1_ID},
{STOP_2_ID},{STOP_1_ID}
{STOP_3_ID},
{STOP_4_ID},
{STOP_5_ID},
-- transfers.txt --
from_stop_id,to_stop_id,transfer_type,min_transfer_time
{STOP_1_ID},{STOP_3_ID},2,300
{STOP_2_ID},{STOP_4_ID},1,200
{STOP_4_ID},{STOP_2_ID},1,100
"""

TRANSFER_1 = client.Transfer(
    id=f"{STOP_1_ID}_to_{STOP_3_ID}",
    fromStop=client.StopReference(id=STOP_1_ID),
    toStop=client.StopReference(id=STOP_3_ID),
    type="REQUIRES_TIME",
    minTransferTime=300,
)
TRANSFER_2 = client.Transfer(
    id=f"{STOP_2_ID}_to_{STOP_4_ID}",
    fromStop=client.StopReference(id=STOP_2_ID),
    toStop=client.StopReference(id=STOP_4_ID),
    type="TIMED",
    minTransferTime=200,
)
TRANSFER_3 = client.Transfer(
    id=f"{STOP_4_ID}_to_{STOP_2_ID}",
    fromStop=client.StopReference(id=STOP_4_ID),
    toStop=client.StopReference(id=STOP_2_ID),
    type="TIMED",
    minTransferTime=100,
)


def test_get_system(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, GTFS_STATIC_TXTAR)

    system = transiter_client.get_system(system_id)
    assert system.transfers == client.ChildResources(
        count=3, path=f"systems/{system_id}/transfers"
    )


def test_list_transfers(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, GTFS_STATIC_TXTAR)

    got_list_transfers = transiter_client.list_transfers(system_id)
    assert got_list_transfers.transfers == [
        TRANSFER_1,
        TRANSFER_2,
        TRANSFER_3,
    ]


def test_get_transfer(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
):
    install_system(system_id, GTFS_STATIC_TXTAR)

    for want_transfer in [
        TRANSFER_1,
        TRANSFER_2,
        TRANSFER_3,
    ]:
        got_transfer = transiter_client.get_transfer(system_id, want_transfer.id)
        assert got_transfer == want_transfer


@pytest.mark.parametrize(
    "stop_id,want_transfers",
    [
        # No transfers
        (STOP_5_ID, []),
        # Single simple transfer
        (STOP_4_ID, [TRANSFER_3]),
        # The next two cases indicate a bug in Transiter.
        # Transfers for stations apply to all child stops, but not the other way around.
        # When querying transfers for stop 1, the transfers for stop 2 should _not_ be returned.
        # When querying transfers for stop 2, the transfers for stop 1 _should_ be returned.
        # TODO: fix the bug
        (STOP_1_ID, [TRANSFER_1, TRANSFER_2]),
        (STOP_2_ID, [TRANSFER_2]),
    ],
)
def test_transfers_at_stop(
    system_id,
    install_system,
    transiter_client: client.TransiterClient,
    stop_id,
    want_transfers,
):
    install_system(system_id, GTFS_STATIC_TXTAR)

    stop = transiter_client.get_stop(system_id, stop_id)
    # TODO: transfers are not returned in order. This is bug.
    stop.transfers.sort(key=lambda transfer: transfer.id)
    assert stop.transfers == want_transfers
