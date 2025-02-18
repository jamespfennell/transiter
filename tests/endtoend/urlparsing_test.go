package endtoend

import (
	"fmt"
	"net/url"
	"testing"

	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

type host string

const (
	adminHost  host = "admin"
	publicHost host = "public"
)

func TestURLParsing(t *testing.T) {
	for _, tc := range []struct {
		name       string
		zipBuilder *testutils.ZipBuilder
		test       func(t *testing.T, client *transiterclient.TransiterClient, systemID string)
	}{
		{
			name: "stop with reserved url characters",
			zipBuilder: fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
				"stops.txt",
				"stop_id,stop_name",
				"$stop_1 / $%^?,Stop 1",
			),
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotStop, err := client.GetStop(systemID, EncodePathParam("$stop_1 / $%^?"))
				if err != nil {
					t.Fatalf("failed to get stop: %v", err)
				}
				testutils.AssertEqual(t, gotStop.ID, "$stop_1 / $%^?")
				testutils.AssertEqual(t, gotStop.Name, "Stop 1")
			},
		},
	} {
		for _, host := range []host{adminHost, publicHost} {
			testName := fmt.Sprintf("%s/%s/%s", "url_parsing", tc.name, host)
			t.Run(testName, func(t *testing.T) {
				systemID, _, _ := fixtures.InstallSystem(t, tc.zipBuilder.MustBuild())
				transiterClient := fixtures.GetTransiterClient(t)
				if host == adminHost {
					transiterClient.UseAdminHost()
				} else {
					transiterClient.UsePublicHost()
				}
				tc.test(t, transiterClient, systemID)
			})
		}
	}
}

func EncodePathParam(s string) string {
	return url.PathEscape(s)
}
