package endtoend

import (
	"fmt"
	"sort"
	"testing"

	"github.com/jamespfennell/transiter/tests/endtoend/fixtures"
	"github.com/jamespfennell/transiter/tests/endtoend/testutils"
	"github.com/jamespfennell/transiter/tests/endtoend/transiterclient"
)

const (
	Stop1ID = "stop-1-id"
	Stop2ID = "stop-2-id"
	Stop3ID = "stop-3-id"
	Stop4ID = "stop-4-id"
	Stop5ID = "stop-5-id"
)

var Transfer1 = transiterclient.Transfer{
	ID:              fmt.Sprintf("%s_to_%s", Stop1ID, Stop3ID),
	FromStop:        &transiterclient.StopReference{ID: Stop1ID},
	ToStop:          &transiterclient.StopReference{ID: Stop3ID},
	Type:            "REQUIRES_TIME",
	MinTransferTime: 300,
}

var Transfer2 = transiterclient.Transfer{
	ID:              fmt.Sprintf("%s_to_%s", Stop2ID, Stop4ID),
	FromStop:        &transiterclient.StopReference{ID: Stop2ID},
	ToStop:          &transiterclient.StopReference{ID: Stop4ID},
	Type:            "TIMED",
	MinTransferTime: 200,
}

var Transfer3 = transiterclient.Transfer{
	ID:              fmt.Sprintf("%s_to_%s", Stop4ID, Stop2ID),
	FromStop:        &transiterclient.StopReference{ID: Stop4ID},
	ToStop:          &transiterclient.StopReference{ID: Stop2ID},
	Type:            "TIMED",
	MinTransferTime: 100,
}

var TransfersGTFSStaticZip = fixtures.GTFSStaticDefaultZipBuilder().AddOrReplaceFile(
	"stops.txt",
	"stop_id,parent_station",
	fmt.Sprintf("%s,", Stop1ID),
	fmt.Sprintf("%s,%s", Stop2ID, Stop1ID),
	fmt.Sprintf("%s,", Stop3ID),
	fmt.Sprintf("%s,", Stop4ID),
	fmt.Sprintf("%s,", Stop5ID),
).AddOrReplaceFile(
	"transfers.txt",
	"from_stop_id,to_stop_id,transfer_type,min_transfer_time",
	fmt.Sprintf("%s,%s,2,300", Stop1ID, Stop3ID),
	fmt.Sprintf("%s,%s,1,200", Stop2ID, Stop4ID),
	fmt.Sprintf("%s,%s,1,100", Stop4ID, Stop2ID),
).MustBuild()

func TestTransfers(t *testing.T) {
	for _, tc := range []struct {
		name string
		test func(t *testing.T, client *transiterclient.TransiterClient, systemID string)
	}{
		{
			name: "get system",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotSystem, err := client.GetSystem(systemID)
				if err != nil {
					t.Fatalf("failed to get system: %v", err)
				}
				testutils.AssertEqual(t, gotSystem.Transfers, &transiterclient.ChildResources{
					Count: 3,
					Path:  fmt.Sprintf("systems/%s/transfers", systemID),
				})
			},
		},
		{
			name: "list transfers",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				gotListTransfers, err := client.ListTransfers(systemID)
				if err != nil {
					t.Fatalf("failed to list transfers: %v", err)
				}
				testutils.AssertEqual(t, gotListTransfers.Transfers, []transiterclient.Transfer{
					Transfer1,
					Transfer2,
					Transfer3,
				})
			},
		},
		{
			name: "get transfer",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				for _, wantTransfer := range []transiterclient.Transfer{
					Transfer1,
					Transfer2,
					Transfer3,
				} {
					gotTransfer, err := client.GetTransfer(systemID, wantTransfer.ID)
					if err != nil {
						t.Fatalf("failed to get transfer %s: %v", wantTransfer.ID, err)
					}
					testutils.AssertEqual(t, gotTransfer, &wantTransfer)
				}
			},
		},
		{
			name: "transfers at stop",
			test: func(t *testing.T, client *transiterclient.TransiterClient, systemID string) {
				type testCase struct {
					stopID        string
					wantTransfers []transiterclient.Transfer
				}

				for _, tc := range []testCase{
					{
						// No transfers
						stopID:        Stop5ID,
						wantTransfers: []transiterclient.Transfer{},
					},
					{
						// Single simple transfer
						stopID:        Stop4ID,
						wantTransfers: []transiterclient.Transfer{Transfer3},
					},
					{
						// The next two cases indicate a bug in Transiter.
						// Transfers for stations apply to all child stops, but not the other way around.
						// When querying transfers for stop 1, the transfers for stop 2 should _not_ be returned.
						// When querying transfers for stop 2, the transfers for stop 1 _should_ be returned.
						// TODO: fix the bug
						stopID:        Stop1ID,
						wantTransfers: []transiterclient.Transfer{Transfer1, Transfer2},
					},
					{
						stopID:        Stop2ID,
						wantTransfers: []transiterclient.Transfer{Transfer2},
					},
				} {
					gotStop, err := client.GetStop(systemID, tc.stopID)
					if err != nil {
						t.Fatalf("failed to get stop %s: %v", tc.stopID, err)
					}

					gotTransfers := gotStop.Transfers
					// TODO: transfers are not returned in order. This is bug.
					sort.Slice(gotTransfers, func(i, j int) bool {
						return gotTransfers[i].ID < gotTransfers[j].ID
					})
					testutils.AssertEqual(t, gotTransfers, tc.wantTransfers)
				}
			},
		},
	} {
		testName := fmt.Sprintf("%s/%s", "transfers", tc.name)
		t.Run(testName, func(t *testing.T) {
			systemID, _, _ := fixtures.InstallSystem(t, TransfersGTFSStaticZip)
			transiterClient := fixtures.GetTransiterClient(t)
			tc.test(t, transiterClient, systemID)
		})
	}
}
