// Package csv is a wrapper around the stdlib csv library that provides a nice API for the GTFS static parser.
//
// Because, of course, everything can be solved with another layer of indirection.
package csv

import (
	"encoding/csv"
	"fmt"
	"io"
)

type File struct {
	headerMap map[string]int
	rows      [][]string
}

func New(reader io.Reader) (*File, error) {
	csvReader := csv.NewReader(reader)
	records, err := csvReader.ReadAll()
	if err != nil {
		return nil, err
	}
	if len(records) == 0 {
		return nil, fmt.Errorf("file contains no rows")
	}
	m := map[string]int{}
	for i, colHeader := range records[0] {
		m[colHeader] = i
	}
	return &File{
		headerMap: m,
		rows:      records[1:],
	}, nil
}

func (p *File) Iter() *Iterator {
	return &Iterator{
		file: p,
		pos:  -1,
	}
}

type Iterator struct {
	file *File
	pos  int
}

func (i *Iterator) Next() bool {
	i.pos += 1
	return i.pos < len(i.file.rows)
}

func (i *Iterator) Get() *Row {
	return &Row{
		file:  i.file,
		cells: i.file.rows[i.pos],
	}
}

type Row struct {
	file        *File
	cells       []string
	missingKeys []string
}

func (r *Row) Get(key string) string {
	i, ok := r.file.headerMap[key]
	if !ok || r.cells[i] == "" {
		r.missingKeys = append(r.missingKeys, key)
		return ""
	}
	return r.cells[i]

}

func (r *Row) GetOr(key string, fallback string) string {
	i, ok := r.file.headerMap[key]
	if !ok {
		return fallback
	}
	return r.cells[i]
}

func (r *Row) GetOrCalculate(key string, f func() string) string {
	i, ok := r.file.headerMap[key]
	if !ok {
		return f()
	}
	return r.cells[i]
}

func (r *Row) GetOptional(key string) *string {
	i, ok := r.file.headerMap[key]
	if !ok || r.cells[i] == "" {
		return nil
	}
	return &r.cells[i]
}

func (r Row) MissingKeys() []string {
	return r.missingKeys
}
