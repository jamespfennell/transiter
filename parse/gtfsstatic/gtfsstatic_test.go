package gtfsstatic

import (
	"archive/zip"
	"bytes"
	"context"
	"fmt"
	"io"
	"reflect"
	"testing"

	"github.com/jamespfennell/transiter/parse"
)

func TestParse(t *testing.T) {
	for i, tc := range []struct {
		content  []byte
		expected *parse.Result
	}{
		{
			newZipBuilder().add(
				"agency.txt",
				"agency_id,agency_name,agency_url,agency_timezone\na,b,c,d",
			).build(),
			&parse.Result{
				Agencies: []parse.Agency{
					{
						Id:       "a",
						Name:     "b",
						Url:      "c",
						Timezone: "b",
					},
				},
			},
		},
		{
			newZipBuilder().add(
				"agency.txt",
				"agency_id,agency_name,agency_url,agency_timezone\na,b,c,d,e,f,g,h",
			).build(),
			&parse.Result{
				Agencies: []parse.Agency{
					{
						Id:       "a",
						Name:     "b",
						Url:      "c",
						Timezone: "b",
						Language: ptr("e"),
						Phone:    ptr("f"),
						FareUrl:  ptr("g"),
						Email:    ptr("h"),
					},
				},
			},
		},
	} {
		t.Run(fmt.Sprintf("%d", i), func(t *testing.T) {
			parser := &Parser{}
			actual, err := parser.Parse(context.Background(), tc.content)
			if err != nil {
				t.Errorf("error when parsing: %s", err)
			}
			if reflect.DeepEqual(actual, tc.expected) {
				t.Errorf("not the same: %v != %v", actual.Agencies[0], tc.expected)
			}
		})
	}
}

type zipBuilder struct {
	m map[string]string
}

func newZipBuilder() *zipBuilder {
	return &zipBuilder{m: map[string]string{}}
}

func (z *zipBuilder) add(fileName, fileContent string) *zipBuilder {
	z.m[fileName] = fileContent
	return z
}

func (z *zipBuilder) build() []byte {
	var b bytes.Buffer
	zipWriter := zip.NewWriter(&b)
	for fileName, fileContent := range z.m {
		fileWriter, err := zipWriter.Create(fileName)
		if err != nil {
			panic(err)
		}
		if _, err := io.Copy(fileWriter, bytes.NewBufferString(fileContent)); err != nil {
			panic(err)
		}
	}
	if err := zipWriter.Close(); err != nil {
		panic(err)
	}
	return b.Bytes()
}

func ptr(s string) *string {
	return &s
}
