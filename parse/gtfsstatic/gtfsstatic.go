package gtfsstatic

import (
	"archive/zip"
	"bytes"
	"context"
	"fmt"
	"log"

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
	for _, file := range reader.File {
		switch file.Name {
		case "agency.txt":
			records, err := readCsvFile(file)
			if err != nil {
				continue
			}
			result.Agencies = parseAgencies(records)
		}
		fmt.Println(file.Name)
	}
	return result, nil
}

func readCsvFile(zipFile *zip.File) (*csv.File, error) {
	content, err := zipFile.Open()
	if err != nil {
		return nil, err
	}
	defer content.Close()
	return csv.New(content)
}

func parseAgencies(csv *csv.File) []parse.Agency {
	var agencies []parse.Agency
	iter := csv.Iter()
	for iter.Next() {
		row := iter.Get()
		agency := parse.Agency{
			Id: row.GetOr("agency_id", func() string {
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
