// Package nyctsubwaycsv contains logic for updating the stop headsign rules from the NYCT CSV file.
package nyctsubwaycsv

import (
	"bytes"
	"context"
	"encoding/csv"
	"fmt"
	"strings"

	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update/common"
)

func Update(ctx context.Context, updateCtx common.UpdateContext, rules []StopHeadsignRule) error {
	if err := updateCtx.Querier.DeleteStopHeadsignRules(ctx, updateCtx.FeedPk); err != nil {
		return err
	}
	stopIDsSet := map[string]bool{}
	var stopIDs []string
	for _, rule := range rules {
		if stopIDsSet[rule.stopID] {
			continue
		}
		stopIDsSet[rule.stopID] = true
		stopIDs = append(stopIDs, rule.stopID)
	}
	stopIDToPk, err := dbwrappers.MapStopIDToPkInSystem(ctx, updateCtx.Querier, updateCtx.SystemPk, stopIDs)
	if err != nil {
		return err
	}
	for i, rule := range rules {
		stopPk, ok := stopIDToPk[rule.stopID]
		if !ok {
			continue
		}
		if err := updateCtx.Querier.InsertStopHeadSignRule(ctx, db.InsertStopHeadSignRuleParams{
			FeedPk:   updateCtx.FeedPk,
			Priority: int32(i),
			StopPk:   stopPk,
			Track:    convert.NullString(rule.track),
			Headsign: rule.headsign,
		}); err != nil {
			return err
		}
	}
	return nil
}

type StopHeadsignRule struct {
	stopID   string
	track    *string
	headsign string
}

func Parse(content []byte) ([]StopHeadsignRule, error) {
	csvReader := csv.NewReader(bytes.NewReader(content))
	records, err := csvReader.ReadAll()
	if err != nil {
		return nil, err
	}
	if len(records) == 0 {
		return nil, fmt.Errorf("subway.csv file contains no header row")
	}
	stopIDCol := -1
	northHeadsignCol := -1
	southHeadsignCol := -1
	for i, header := range records[0] {
		// In October 2023 the MTA announced a change to the URL to the stations.csv file [1],
		// but they also changed the format a little bit. In the old stations.csv file the header
		// cells were in the form "North Direction Label", while in the new file the cells are
		// in the form "north_direction_label". To handle both simultaneously we normalize to
		// the new format.
		//
		// [1] https://groups.google.com/g/mtadeveloperresources/c/0J07edOWH-Q
		header = strings.ReplaceAll(strings.ToLower(header), " ", "_")
		switch header {
		case "gtfs_stop_id":
			stopIDCol = i
		case "north_direction_label":
			northHeadsignCol = i
		case "south_direction_label":
			southHeadsignCol = i
		}
	}
	if stopIDCol < 0 {
		return nil, fmt.Errorf("subway.csv file is missing the stop ID column")
	}
	if northHeadsignCol < 0 {
		return nil, fmt.Errorf("subway.csv file is missing the north headsign/label column")
	}
	if southHeadsignCol < 0 {
		return nil, fmt.Errorf("subway.csv file is missing the south headsign/label column")
	}
	rules := customRules()
	customStopIDs := map[string]bool{}
	for _, rule := range rules {
		customStopIDs[rule.stopID] = true
	}
	for _, row := range records[1:] {
		northStopID := row[stopIDCol] + "N"
		if headsign, ok := cleanHeadsign(row[northHeadsignCol]); ok && !customStopIDs[northStopID] {
			rules = append(rules, StopHeadsignRule{
				stopID:   northStopID,
				headsign: headsign,
			})
		}
		southStopID := row[stopIDCol] + "S"
		if headsign, ok := cleanHeadsign(row[southHeadsignCol]); ok && !customStopIDs[southStopID] {
			rules = append(rules, StopHeadsignRule{
				stopID:   southStopID,
				headsign: headsign,
			})
		}
	}
	return rules, nil
}

func cleanHeadsign(s string) (string, bool) {
	s = strings.TrimSpace(s)
	if s == "" {
		return "", false
	}
	return strings.ReplaceAll(s, "&", "and"), true
}

const (
	eastSideAndQueens = "East Side and Queens"
	manhattan         = "Manhattan"
	rockaways         = "Euclid - Lefferts - Rockaways" // To be consistent with the MTA
	uptown            = "Uptown"
	uptownAndTheBronx = "Uptown and The Bronx"
	queens            = "Queens"
)

func customRules() []StopHeadsignRule {
	var rules []StopHeadsignRule
	for _, g := range []struct {
		stopID          string
		track           string
		trackHeadsign   string
		defaultHeadsign string
	}{
		{
			// Hoyt-Schermerhorn Sts station (northbound)
			stopID:          "A42N",
			track:           "E2",
			trackHeadsign:   "Court Sq, Queens",
			defaultHeadsign: manhattan,
		},
		{
			// Hoyt-Schermerhorn Sts station (southbound)
			stopID:          "A42S",
			track:           "E1",
			trackHeadsign:   "Church Av, Brooklyn",
			defaultHeadsign: rockaways,
		},
		{
			// Jay St-Metrotech
			stopID:          "A41S",
			track:           "B1",
			trackHeadsign:   "Coney Island",
			defaultHeadsign: rockaways,
		},
		{
			// 50th St
			stopID:          "A25N",
			track:           "D4",
			trackHeadsign:   eastSideAndQueens,
			defaultHeadsign: uptownAndTheBronx,
		},
		{
			// 47-50 Sts-Rockefeller Ctr
			stopID:          "D15N",
			track:           "B2",
			trackHeadsign:   eastSideAndQueens,
			defaultHeadsign: uptownAndTheBronx,
		},
		{
			// 57 St-7 Av
			stopID:          "R14N",
			track:           "A4",
			trackHeadsign:   uptown,
			defaultHeadsign: queens,
		},

		{
			// Lexington Av/63 St
			stopID:          "B08N",
			track:           "T2",
			trackHeadsign:   queens,
			defaultHeadsign: uptown,
		},
		{
			// 7 Av
			stopID:          "D14N",
			track:           "D4",
			trackHeadsign:   eastSideAndQueens,
			defaultHeadsign: uptownAndTheBronx,
		},
		{
			// Prospect Park
			stopID:          "D26N",
			track:           "A2",
			trackHeadsign:   "Franklin Avenue",
			defaultHeadsign: manhattan,
		},
	} {
		g := g
		rules = append(rules,
			StopHeadsignRule{
				stopID:   g.stopID,
				track:    &g.track,
				headsign: g.trackHeadsign,
			},
			StopHeadsignRule{
				stopID:   g.stopID,
				headsign: g.defaultHeadsign,
			},
		)
	}
	return rules
}
