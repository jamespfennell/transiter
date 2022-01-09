package gtfsstatic

import (
	"archive/zip"
	"bytes"
	"context"
	"io"
	"reflect"
	"testing"

	"github.com/jamespfennell/transiter/parse"
)

func TestParse(t *testing.T) {
	defaultAgency := parse.Agency{
		Id:       "a",
		Name:     "b",
		Url:      "c",
		Timezone: "d",
	}
	otherAgency := parse.Agency{
		Id:       "e",
		Name:     "f",
		Url:      "g",
		Timezone: "h",
	}
	for _, tc := range []struct {
		desc     string
		content  []byte
		expected *parse.Result
	}{
		{
			"agency with only required fields",
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
						Timezone: "d",
					},
				},
			},
		},
		{
			"agency with all fields",
			newZipBuilder().add(
				"agency.txt",
				"agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone,agency_fare_url,agency_email\na,b,c,d,e,f,g,h",
			).build(),
			&parse.Result{
				Agencies: []parse.Agency{
					{
						Id:       "a",
						Name:     "b",
						Url:      "c",
						Timezone: "d",
						Language: ptr("e"),
						Phone:    ptr("f"),
						FareUrl:  ptr("g"),
						Email:    ptr("h"),
					},
				},
			},
		},
		{
			"route with only required fields",
			newZipBuilder().add(
				"agency.txt",
				"agency_id,agency_name,agency_url,agency_timezone\na,b,c,d",
			).add(
				"routes.txt",
				"route_id,route_type\na,3",
			).build(),
			&parse.Result{
				Agencies: []parse.Agency{defaultAgency},
				Routes: []parse.Route{
					{
						Id:        "a",
						Agency:    &defaultAgency,
						Color:     "FFFFFF",
						TextColor: "000000",
						Type:      parse.Bus,
					},
				},
			},
		},
		{
			"route with all fields",
			newZipBuilder().add(
				"agency.txt",
				"agency_id,agency_name,agency_url,agency_timezone\na,b,c,d",
			).add(
				"routes.txt",
				"route_id,route_color,route_text_color,route_short_name,"+
					"route_long_name,route_desc,route_type,route_url,route_sort_order,continuous_pickup,continuous_dropoff\n"+
					"a,b,c,e,f,g,2,h,5,0,2",
			).build(),
			&parse.Result{
				Agencies: []parse.Agency{defaultAgency},
				Routes: []parse.Route{
					{
						Id:                "a",
						Agency:            &defaultAgency,
						Color:             "b",
						TextColor:         "c",
						ShortName:         ptr("e"),
						LongName:          ptr("f"),
						Description:       ptr("g"),
						Type:              parse.Rail,
						Url:               ptr("h"),
						SortOrder:         intPtr(5),
						ContinuousPickup:  parse.Continuous,
						ContinuousDropOff: parse.PhoneAgency,
					},
				},
			},
		},
		{
			"route with matching specified agency",
			newZipBuilder().add(
				"agency.txt",
				"agency_id,agency_name,agency_url,agency_timezone\na,b,c,d\ne,f,g,h",
			).add(
				"routes.txt",
				"route_id,route_type,agency_id\na,3,e",
			).build(),
			&parse.Result{
				Agencies: []parse.Agency{defaultAgency, otherAgency},
				Routes: []parse.Route{
					{
						Id:        "a",
						Agency:    &otherAgency,
						Color:     "FFFFFF",
						TextColor: "000000",
						Type:      parse.Bus,
					},
				},
			},
		},
	} {
		t.Run(tc.desc, func(t *testing.T) {
			parser := &Parser{}
			actual, err := parser.Parse(context.Background(), tc.content)
			if err != nil {
				t.Errorf("error when parsing: %s", err)
			}
			if !reflect.DeepEqual(actual, tc.expected) {
				t.Errorf("not the same: \n%+v != \n%+v", actual, tc.expected)
			}
		})
	}
}

type zipBuilder struct {
	m map[string]string
}

func newZipBuilder() *zipBuilder {
	return (&zipBuilder{m: map[string]string{}}).add(
		"agency.txt", "agency_id,agency_name,agency_url,agency_timezone",
	).add(
		"routes.txt", "route_id,route_type",
	)
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

func intPtr(i int32) *int32 {
	return &i
}
