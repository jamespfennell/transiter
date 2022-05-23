// Package nyctsubwaycsv contains logic for updating the stop headsign rules from the NYCT CSV file.
package nyctsubwaycsv

import (
	"bytes"
	"context"
	"encoding/csv"
	"fmt"
	"strings"

	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/update/common"
)

func ParseAndUpdate(ctx context.Context, updateCtx common.UpdateContext, content []byte) error {
	rules, err := parse(content)
	if err != nil {
		return err
	}
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
			SourcePk: updateCtx.UpdatePk,
			Priority: int32(i),
			StopPk:   stopPk,
			Headsign: rule.headsign,
		}); err != nil {
			return err
		}
	}
	return nil
}

type rule struct {
	stopID   string
	track    *string
	headsign string
}

func parse(content []byte) ([]rule, error) {
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
		switch header {
		case "GTFS Stop ID":
			stopIDCol = i
		case "North Direction Label":
			northHeadsignCol = i
		case "South Direction Label":
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
			rules = append(rules, rule{
				stopID:   northStopID,
				headsign: headsign,
			})
		}
		southStopID := row[stopIDCol] + "S"
		if headsign, ok := cleanHeadsign(row[southHeadsignCol]); ok && !customStopIDs[southStopID] {
			rules = append(rules, rule{
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

func customRules() []rule {
	eastSideAndQueens := "East Side and Queens"
	manhattan := "Manhattan"
	rockaways := "Euclid - Lefferts - Rockaways" // To be consistent with the MTA
	uptown := "Uptown"
	uptownAndTheBronx := "Uptown and The Bronx"
	queens := "Queens"

	var rules []rule
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
			rule{
				stopID:   g.stopID,
				track:    &g.track,
				headsign: g.trackHeadsign,
			},
			rule{
				stopID:   g.stopID,
				headsign: g.defaultHeadsign,
			},
		)
	}
	return rules
}
