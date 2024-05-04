from . import client


def test_agencies(
    system_id, install_system_using_txtar, transiter_client: client.TransiterClient
):
    gtfs_static_txtar = """
    -- agency.txt --
    agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone,agency_fare_url,agency_email
    AgencyId,AgencyName,AgencyUrl,AgencyTimezone,AgencyLanguage,AgencyPhone,AgencyFareUrl,AgencyEmail
    """
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

    install_system_using_txtar(system_id, gtfs_static_txtar)

    got_system = transiter_client.get_system(system_id)
    assert got_system.agencies == client.ChildResources(
        count=1, path=f"systems/{system_id}/agencies"
    )

    got_agencies = transiter_client.list_agencies(system_id)
    assert got_agencies.agencies == [want_agency]

    got_agency = transiter_client.get_agency(system_id, "AgencyId")
    assert got_agency == want_agency
