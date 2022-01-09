package gtfsstatic

import (
	"archive/zip"
	"bytes"
	"context"
	"fmt"
	"log"
	"strconv"

	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/csv"
	"github.com/jamespfennell/transiter/parse"
)

type Parser struct {
	Options *config.GtfsStaticOptions
}

func (p Parser) Parse(ctx context.Context, content []byte) (*parse.Result, error) {
	reader, err := zip.NewReader(bytes.NewReader(content), int64(len(content)))
	if err != nil {
		return nil, err
	}
	result := &parse.Result{}
	fileNameToFile := map[string]*zip.File{}
	for _, file := range reader.File {
		fileNameToFile[file.Name] = file
	}
	for _, table := range []struct {
		fileName string
		action   func(file *csv.File)
	}{
		{
			"agency.txt",
			func(file *csv.File) {
				result.Agencies = parseAgencies(file)
			},
		},
		{
			"routes.txt",
			func(file *csv.File) {
				result.Routes = parseRoutes(file, result.Agencies)
			},
		},
	} {
		file, err := readCsvFile(fileNameToFile, table.fileName)
		if err != nil {
			return nil, err
		}
		table.action(file)
	}
	return result, nil
}

func readCsvFile(fileNameToFile map[string]*zip.File, fileName string) (*csv.File, error) {
	zipFile := fileNameToFile[fileName]
	if zipFile == nil {
		return nil, fmt.Errorf("no %q file in GTFS static feed", fileName)
	}
	content, err := zipFile.Open()
	if err != nil {
		return nil, err
	}
	defer content.Close()
	f, err := csv.New(content)
	if err != nil {
		return nil, fmt.Errorf("failed to parse %q: %w", fileName, err)
	}
	return f, nil
}

func parseAgencies(csv *csv.File) []parse.Agency {
	var agencies []parse.Agency
	iter := csv.Iter()
	for iter.Next() {
		row := iter.Get()
		agency := parse.Agency{
			Id: row.GetOrCalculate("agency_id", func() string {
				// TODO: support specifying the agency ID in the GTFS static parser settings
				return fmt.Sprintf("%s_id", row.Get("agency_name"))
			}),
			Name:     row.Get("agency_name"),
			Url:      row.Get("agency_url"),
			Timezone: row.Get("agency_timezone"),
			Language: row.GetOptional("agency_lang"),
			Phone:    row.GetOptional("agency_phone"),
			FareUrl:  row.GetOptional("agency_fare_url"),
			Email:    row.GetOptional("agency_email"),
		}
		if missingKeys := row.MissingKeys(); len(missingKeys) > 0 {
			log.Printf("Skipping agency %+v because of missing keys %s", agency, missingKeys)
			continue
		}
		agencies = append(agencies, agency)
	}
	return agencies
}

func parseRoutes(csv *csv.File, agencies []parse.Agency) []parse.Route {
	var routes []parse.Route
	iter := csv.Iter()
	for iter.Next() {
		row := iter.Get()
		agencyId := row.GetOptional("agency_id")
		var agency *parse.Agency
		if agencyId != nil {
			for i := range agencies {
				if agencies[i].Id == *agencyId {
					agency = &agencies[i]
					break
				}
			}
			if agency == nil {
				log.Printf("skipping route %s: no match for agency ID %s", row.Get("route_id"), *agencyId)
				continue
			}
		} else if len(agencies) == 1 {
			// In GTFS static if there is a single agency, a route's agency ID field can be omitted in
			// which case the route's agency is the unique agency in the feed.
			agency = &agencies[0]
		} else {
			log.Printf("skipping route %s: no agency ID provided but no unique agency", row.Get("route_id"))
			continue
		}
		route := parse.Route{
			Id:                row.Get("route_id"),
			Agency:            agency,
			Color:             row.GetOr("route_color", "FFFFFF"),
			TextColor:         row.GetOr("route_text_color", "000000"),
			ShortName:         row.GetOptional("route_short_name"),
			LongName:          row.GetOptional("route_long_name"),
			Description:       row.GetOptional("route_desc"),
			Type:              parseRouteType(row.Get("route_type")),
			Url:               row.GetOptional("route_url"),
			SortOrder:         parseRouteSortOrder(row.GetOptional("route_sort_order")),
			ContinuousPickup:  parseRoutePolicy(row.GetOptional("continuous_pickup")),
			ContinuousDropOff: parseRoutePolicy(row.GetOptional("continuous_dropoff")),
		}
		if missingKeys := row.MissingKeys(); len(missingKeys) > 0 {
			log.Printf("Skipping route %+v because of missing keys %s", route, missingKeys)
			continue
		}
		routes = append(routes, route)
	}
	return routes
}

func parseRouteType(raw string) parse.RouteType {
	i, err := strconv.Atoi(raw)
	if err != nil {
		return parse.UnknownRouteType
	}
	t, _ := parse.NewRouteType(i)
	return t
}

func parseRouteSortOrder(raw *string) *int32 {
	if raw == nil {
		return nil
	}
	i, err := strconv.Atoi(*raw)
	if err != nil {
		return nil
	}
	i32 := int32(i)
	return &i32
}

func parseRoutePolicy(raw *string) parse.RoutePolicy {
	if raw == nil {
		return parse.NotAllowed
	}
	i, err := strconv.Atoi(*raw)
	if err != nil {
		return parse.NotAllowed
	}
	return parse.NewRoutePolicy(i)
}
