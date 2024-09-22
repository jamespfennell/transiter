package nyctsubwaycsv

import (
	"context"
	"fmt"
	"io"
	"math"
	"math/big"
	"os"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/db/types"
	"github.com/jamespfennell/transiter/internal/db/dbtesting"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update/common"
	"github.com/jamespfennell/transiter/internal/update/static"
	"golang.org/x/exp/slog"
)

func TestParse(t *testing.T) {
	for _, tc := range []struct {
		name        string
		csvDataPath string
		want        *NyctSubwayStopCsvData
	}{
		{
			name:        "empty",
			csvDataPath: "testdata/MTA_Subway_Stations.csv",
			want: &NyctSubwayStopCsvData{
				stopHeadsignRules: []StopHeadsignRule{
					{stopID: "R01N", headsign: "Last Stop"},
					{stopID: "R01S", headsign: "Manhattan"},
					{stopID: "R03N", headsign: "Astoria"},
					{stopID: "R03S", headsign: "Manhattan"},
					{stopID: "R15N", headsign: "Uptown"},
					{stopID: "R15S", headsign: "Downtown"},
					// A25N has a custom headsign rule
					{stopID: "A25S", headsign: "Downtown"},
				},
				stopAccessibilityData: []StopAccessibilityInfo{
					{stopID: "R01", wheelchairBoarding: gtfs.WheelchairBoarding_NotPossible},
					{stopID: "R01N", wheelchairBoarding: gtfs.WheelchairBoarding_NotPossible},
					{stopID: "R01S", wheelchairBoarding: gtfs.WheelchairBoarding_NotPossible},
					{stopID: "R03", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
					{stopID: "R03N", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
					{stopID: "R03S", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
					{stopID: "R15", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
					{stopID: "R15N", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
					{stopID: "R15S", wheelchairBoarding: gtfs.WheelchairBoarding_NotPossible},
					{stopID: "A25", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
					{stopID: "A25N", wheelchairBoarding: gtfs.WheelchairBoarding_NotPossible},
					{stopID: "A25S", wheelchairBoarding: gtfs.WheelchairBoarding_Possible},
				},
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			// Read the bytes from the file
			content, err := readFileBytes(tc.csvDataPath)
			if err != nil {
				t.Fatalf("readFileBytes() err = %v, want = nil", err)
			}

			got, err := Parse(content)
			if err != nil {
				t.Fatalf("Parse() err = %v, want = nil", err)
			}

			// Prepend the custom headsign rules to the expected rules
			customRules := customRules()
			tc.want.stopHeadsignRules = append(customRules, tc.want.stopHeadsignRules...)

			if diff := cmp.Diff(got, tc.want, cmp.AllowUnexported(NyctSubwayStopCsvData{}, StopHeadsignRule{}, StopAccessibilityInfo{})); diff != "" {
				t.Errorf("Parse() got = %v, want = %v, diff = %s", got, tc.want, diff)
			}
		})
	}
}

type AccessibilityUpdateSource int

const (
	NYCT_SUBWAY_CSV AccessibilityUpdateSource = iota
	GTFS_STATIC
	UNSPECIFIED
)

func TestUpdate(t *testing.T) {
	for _, tc := range []struct {
		name               string
		staticGtfsDataPath string
		csvDataPath        *string
		updates            []NyctSubwayStopCsvData
		checkHeadsignRules *bool
		wantHeadsignRules  []db.ListStopHeadsignRulesForFeedRow
		wantStops          []db.Stop
		accesibilitySource AccessibilityUpdateSource
	}{
		{
			name:               "accessibility info from csv",
			staticGtfsDataPath: "testdata/nyct_subway.zip",
			csvDataPath:        ptr("testdata/MTA_Subway_Stations.csv"),
			wantHeadsignRules: []db.ListStopHeadsignRulesForFeedRow{
				{StopID: "R01N", Priority: 18, Headsign: "Last Stop"},
				{StopID: "R01S", Priority: 19, Headsign: "Manhattan"},
				{StopID: "R03N", Priority: 20, Headsign: "Astoria"},
				{StopID: "R03S", Priority: 21, Headsign: "Manhattan"},
				{StopID: "R15N", Priority: 22, Headsign: "Uptown"},
				{StopID: "R15S", Priority: 23, Headsign: "Downtown"},
				{StopID: "A25N", Priority: 7, Headsign: "Uptown and The Bronx"},
				{
					StopID:   "A25N",
					Priority: 6,
					Track:    pgtype.Text{String: "D4", Valid: true},
					Headsign: "East Side and Queens",
				},
				{StopID: "A25S", Priority: 24, Headsign: "Downtown"},
			},
			wantStops: []db.Stop{

				{
					ID:       "103",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "STATION",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:       "103N",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "PLATFORM",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:       "103S",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "PLATFORM",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:                 "A25",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "A25N",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "A25S",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "R01",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R01N",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R01S",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R03",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R03N",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R03S",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R15",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
				{
					ID:                 "R15N",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Bool: true, Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
				{
					ID:                 "R15S",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: true},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
			},
		},
		{
			name:               "accessibility info from gtfs static",
			staticGtfsDataPath: "testdata/nyct_subway.zip",
			csvDataPath:        ptr("testdata/MTA_Subway_Stations.csv"),
			checkHeadsignRules: ptr(false),
			accesibilitySource: GTFS_STATIC,
			wantStops: []db.Stop{
				{
					ID:       "103",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "STATION",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:       "103N",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "PLATFORM",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:       "103S",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "PLATFORM",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:                 "A25",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "A25N",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "A25S",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "R01",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R01N",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R01S",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R03",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R03N",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R03S",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R15",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
				{
					ID:                 "R15N",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
				{
					ID:                 "R15S",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
			},
		},
		{
			name:               "unspecified accessibility source",
			staticGtfsDataPath: "testdata/nyct_subway.zip",
			csvDataPath:        ptr("testdata/MTA_Subway_Stations.csv"),
			checkHeadsignRules: ptr(false),
			accesibilitySource: UNSPECIFIED,
			wantStops: []db.Stop{
				{
					ID:       "103",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "STATION",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:       "103N",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "PLATFORM",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:       "103S",
					Name:     pgtype.Text{String: "238 St", Valid: true},
					Type:     "PLATFORM",
					Location: types.Geography{Valid: true, Type: 536870913, Longitude: -73.90087, Latitude: 40.884667},
				},
				{
					ID:                 "A25",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "A25N",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "A25S",
					Name:               pgtype.Text{String: "50 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.985984, Latitude: 40.762456},
				},
				{
					ID:                 "R01",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R01N",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R01S",
					Name:               pgtype.Text{String: "Astoria-Ditmars Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.912034, Latitude: 40.775036},
				},
				{
					ID:                 "R03",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R03N",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R03S",
					Name:               pgtype.Text{String: "Astoria Blvd", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.917843, Latitude: 40.770258},
				},
				{
					ID:                 "R15",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "STATION",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
				{
					ID:                 "R15N",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
				{
					ID:                 "R15S",
					Name:               pgtype.Text{String: "49 St", Valid: true},
					Type:               "PLATFORM",
					WheelchairBoarding: pgtype.Bool{Valid: false},
					Location:           types.Geography{Valid: true, Type: 536870913, Longitude: -73.984139, Latitude: 40.759901},
				},
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			querier := dbtesting.NewQuerier(t)
			system := querier.NewSystem("system")
			staticFeed := system.NewFeed("staticFeedID")
			csvFeed := system.NewFeed("csvFeedID")

			ctx := context.Background()
			staticUpdateCtx := common.UpdateContext{
				Querier:  querier,
				SystemPk: system.Data.Pk,
				FeedPk:   staticFeed.Data.Pk,
				FeedConfig: &api.FeedConfig{
					Parser: "GTFS_STATIC",
					NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
						UseAccessibilityInfo: false,
					},
				},
				Logger: slog.Default(),
			}

			if tc.accesibilitySource == GTFS_STATIC {
				staticUpdateCtx.FeedConfig.NyctSubwayOptions.UseAccessibilityInfo = true
			}

			if tc.accesibilitySource == UNSPECIFIED {
				staticUpdateCtx.FeedConfig.NyctSubwayOptions = nil
			}

			// Update static data first
			staticBytes, err := readFileBytes(tc.staticGtfsDataPath)
			if err != nil {
				t.Fatalf("readFileBytes() err = %v, want = nil", err)
			}
			gtfsStaticData, err := gtfs.ParseStatic(staticBytes, gtfs.ParseStaticOptions{})
			if err != nil {
				t.Fatalf("gtfs.ParseStatic() err = %v, want = nil", err)
			}
			err = static.Update(ctx, staticUpdateCtx, gtfsStaticData)
			if err != nil {
				t.Fatalf("Static Update() got = %+v, want = <nil>", err)
			}

			if tc.csvDataPath != nil {
				content, err := readFileBytes(*tc.csvDataPath)
				if err != nil {
					t.Fatalf("readFileBytes() err = %v, want = nil", err)
				}

				csvData, err := Parse(content)
				if err != nil {
					t.Fatalf("Parse() err = %v, want = nil", err)
				}

				// Prepend the CSV data as the first update
				tc.updates = append([]NyctSubwayStopCsvData{*csvData}, tc.updates...)
			}

			for i, update := range tc.updates {
				csvUpdateCtx := common.UpdateContext{
					Querier:  querier,
					SystemPk: system.Data.Pk,
					FeedPk:   csvFeed.Data.Pk,
					FeedConfig: &api.FeedConfig{
						Parser: "NYCT_SUBWAY_CSV",
						NyctSubwayOptions: &api.FeedConfig_NyctSubwayOptions{
							UseAccessibilityInfo: true,
						},
					},
					Logger: slog.Default(),
				}

				if tc.accesibilitySource != NYCT_SUBWAY_CSV {
					csvUpdateCtx.FeedConfig.NyctSubwayOptions.UseAccessibilityInfo = false
				}

				if tc.accesibilitySource == UNSPECIFIED {
					csvUpdateCtx.FeedConfig.NyctSubwayOptions = nil
				}

				err := Update(ctx, csvUpdateCtx, &update)
				if err != nil {
					t.Fatalf("Update(update = %d) got = %+v, want = <nil>", i, err)
				}
			}

			gotStops, _ := listStops(ctx, t, querier, staticUpdateCtx.SystemPk)
			if diff := cmp.Diff(gotStops, tc.wantStops, cmp.Comparer(compareBigInt)); diff != "" {
				t.Errorf("ListStops() got = %v, want = %v, diff = %s", gotStops, tc.wantStops, diff)
			}

			// Check headsign rules if they are expected (on by default if not specified)
			if tc.checkHeadsignRules == nil || *tc.checkHeadsignRules {
				gotHeadsignRules, _ := querier.ListStopHeadsignRulesForFeed(ctx, csvFeed.Data.Pk)
				if diff := cmp.Diff(gotHeadsignRules, tc.wantHeadsignRules, cmp.Comparer(compareBigInt)); diff != "" {
					t.Errorf("ListStopHeadsignRulesForFeed() got = %v, want = %v, diff = %s", gotHeadsignRules, tc.wantHeadsignRules, diff)
				}
			}

			// Do one more update from static feed and verify stops still has accessibility info
			// This is to test that the GTFS static data does not overwrite the accessibility info from the CSV
			err = static.Update(ctx, staticUpdateCtx, gtfsStaticData)
			if err != nil {
				t.Fatalf("Static Update() got = %+v, want = <nil>", err)
			}
			gotStops, _ = listStops(ctx, t, querier, staticUpdateCtx.SystemPk)
			if diff := cmp.Diff(gotStops, tc.wantStops, cmp.Comparer(compareBigInt)); diff != "" {
				t.Errorf("ListStops() got = %v, want = %v, diff = %s", gotStops, tc.wantStops, diff)
			}
		})
	}
}

func listStops(ctx context.Context, t *testing.T, querier db.Querier, systemPk int64) ([]db.Stop, map[string]string) {
	stops, err := querier.ListStops(ctx, db.ListStopsParams{SystemPk: systemPk, NumStops: math.MaxInt32})
	if err != nil {
		t.Errorf("ListStops() err = %v, want = nil", err)
	}
	stopPkToParentPk := map[int64]int64{}
	pkToID := map[int64]string{}
	for i := range stops {
		stop := &stops[i]
		if stop.ParentStopPk.Valid {
			stopPkToParentPk[stop.Pk] = stop.ParentStopPk.Int64
		}
		pkToID[stop.Pk] = stop.ID
		stop.Pk = 0
		stop.ParentStopPk = pgtype.Int8{}
		stop.FeedPk = 0
		stop.SystemPk = 0
	}
	stopIDToParentID := map[string]string{}
	for stopPk, parentPk := range stopPkToParentPk {
		stopIDToParentID[pkToID[stopPk]] = pkToID[parentPk]
	}
	return stops, stopIDToParentID
}

func ptr[T any](t T) *T {
	return &t
}

func compareBigInt(a, b *big.Int) bool {
	return a.Cmp(b) == 0
}

func readFileBytes(filePath string) ([]byte, error) {
	// Open the file
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	// Read the file's contents into a byte slice
	bytes, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	return bytes, nil
}
