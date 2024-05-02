from . import client


def test_transfers(
    system_id,
    install_system_1,
    transiter_client: client.TransiterClient,
):
    install_system_1(system_id)

    system = transiter_client.get_system(system_id)
    assert system.transfers.count == 3

    want_transfers = [
        client.Transfer(
            id="1E_to_2MEX",
            fromStop=client.StopReference(id="1E"),
            toStop=client.StopReference(id="2MEX"),
            type="REQUIRES_TIME",
            minTransferTime=200,
        ),
        client.Transfer(
            id="2COL_to_1C",
            fromStop=client.StopReference(id="2COL"),
            toStop=client.StopReference(id="1C"),
            type="TIMED",
            minTransferTime=300,
        ),
        client.Transfer(
            id="2MEX_to_1E",
            fromStop=client.StopReference(id="2MEX"),
            toStop=client.StopReference(id="1E"),
            type="REQUIRES_TIME",
            minTransferTime=200,
        ),
    ]
    got_list_transfers = transiter_client.list_transfers(system_id)
    assert got_list_transfers.transfers == want_transfers

    for want_transfer in want_transfers:
        got_transfer = transiter_client.get_transfer(system_id, want_transfer.id)
        assert got_transfer == want_transfer

    stop_1 = transiter_client.get_stop(system_id, "2COL")
    assert stop_1.transfers == [want_transfers[1]]

    stop_2 = transiter_client.get_stop(system_id, "2MEX")
    assert stop_2.transfers == [want_transfers[2]]
