package endtoend

import (
	"testing"

	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

func TestAgencies(t *testing.T) {
	gtfsStaticZipBuilder := fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
		"agency.txt",
		"agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone,agency_fare_url,agency_email",
		"AgencyId,AgencyName,AgencyUrl,AgencyTimezone,AgencyLanguage,AgencyPhone,AgencyFareUrl,AgencyEmail",
	)
	systemID, _, _ := fixtures.InstallSystem(t, gtfsStaticZipBuilder.MustBuild())
	transiterClient := fixtures.GetTransiterClient(t)
	system, err := transiterClient.GetSystem(systemID)
	if err != nil {
		t.Fatalf("failed to get system: %v", err)
	}
	if system.Agencies.Count != 1 {
		t.Fatalf("expected 1 agency, got %d", system.Agencies.Count)
	}

	wantAgency := transiterclient.Agency{
		ID:       "AgencyId",
		Name:     "AgencyName",
		URL:      "AgencyUrl",
		Timezone: "AgencyTimezone",
		Language: testutils.Ptr("AgencyLanguage"),
		Phone:    testutils.Ptr("AgencyPhone"),
		FareURL:  testutils.Ptr("AgencyFareUrl"),
		Email:    testutils.Ptr("AgencyEmail"),
		Alerts:   []transiterclient.AlertReference{},
		Routes:   []transiterclient.RouteReference{},
	}

	gotAgencies, err := transiterClient.ListAgencies(systemID)
	if err != nil {
		t.Fatalf("failed to list agencies: %v", err)
	}
	if len(gotAgencies.Agencies) != 1 {
		t.Fatalf("expected 1 agency, got %d", len(gotAgencies.Agencies))
	}

	testutils.AssertEqual(t, gotAgencies.Agencies, []transiterclient.Agency{wantAgency})

	gotAgency, err := transiterClient.GetAgency(systemID, "AgencyId")
	if err != nil {
		t.Fatalf("failed to get agency: %v", err)
	}
	testutils.AssertEqual(t, gotAgency, &wantAgency)
}
