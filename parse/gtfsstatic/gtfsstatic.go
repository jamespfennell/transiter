package gtfsstatic

import (
	"archive/zip"
	"bytes"
	"context"
	"encoding/csv"
	"fmt"
	"log"

	"github.com/jamespfennell/transiter/config"
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

func readCsvFile(file *zip.File) (parsedCsv, error) {
	reader, err := file.Open()
	if err != nil {
		return parsedCsv{}, err
	}
	defer reader.Close()
	csvReader := csv.NewReader(reader)
	records, err := csvReader.ReadAll()
	if err != nil {
		return parsedCsv{}, err
	}
	if len(records) == 0 {
		return parsedCsv{}, fmt.Errorf("file contains no rows")
	}
	m := map[string]int{}
	for i, colHeader := range records[0] {
		m[colHeader] = i
	}
	return parsedCsv{
		headerMap: m,
		rows:      records[1:],
	}, nil
}

type parsedCsv struct {
	headerMap map[string]int
	rows      [][]string
}

func (p *parsedCsv) iter() parsedCsvIter {
	return parsedCsvIter{
		p: p,
		i: -1,
	}
}

type parsedCsvIter struct {
	p *parsedCsv
	i int
}

func (i *parsedCsvIter) next() bool {
	i.i += 1
	return i.i < len(i.p.rows)
}

func (i *parsedCsvIter) get() row {
	return row{
		p: i.p,
		r: i.p.rows[i.i],
	}
}

type row struct {
	p           *parsedCsv
	r           []string
	missingKeys []string
}

func (r *row) get(key string) string {
	i, ok := r.p.headerMap[key]
	if !ok || r.r[i] == "" {
		r.missingKeys = append(r.missingKeys, key)
		return ""
	}
	return r.r[i]
}

func (r *row) getOr(key string, f func() string) string {
	i, ok := r.p.headerMap[key]
	if !ok {
		return f()
	}
	return r.r[i]
}

func (r *row) getOptional(key string) *string {
	i, ok := r.p.headerMap[key]
	if !ok || r.r[i] == "" {
		return nil
	}
	return &r.r[i]
}

func (r *row) MissingKeys() []string {
	return r.missingKeys
}

func parseAgencies(csv parsedCsv) []parse.Agency {
	var agencies []parse.Agency
	iter := csv.iter()
	for iter.next() {
		row := iter.get()
		agency := parse.Agency{
			Id: row.getOr("agency_id", func() string {
				return fmt.Sprintf("%s_id", row.get("agency_name"))
			}),
			Name:     row.get("agency_name"),
			Url:      row.get("agency_url"),
			Timezone: row.get("agency_timezone"),
			Language: row.getOptional("agency_lang"),
			Phone:    row.getOptional("agency_phone"),
			FareUrl:  row.getOptional("agency_fare_url"),
			Email:    row.getOptional("agency_email"),
		}
		if missingKeys := row.MissingKeys(); len(missingKeys) > 0 {
			log.Printf("Skipping agency %+v because of missing keys %s", agency, missingKeys)
			continue
		}
		agencies = append(agencies, agency)
	}
	return agencies
}
