from . import client


def test_agencies(
    system_id, install_system_1, transiter_client: client.TransiterClient
):
    install_system_1(system_id)

    want_agency = client.Agency(
        id="AgencyId",
        name="AgencyName",
        url="AgencyUrl",
        timezone="AgencyTimezone",
        language="AgencyLanguage",
        phone="AgencyPhone",
        fareUrl="AgencyFareUrl",
        email="AgencyEmail",
    )

    got_agencies = transiter_client.list_agencies(system_id)
    assert got_agencies.agencies == [want_agency]

    got_agency = transiter_client.get_agency(system_id, "AgencyId")
    assert got_agency == want_agency
