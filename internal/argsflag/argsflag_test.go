package argsflag

import (
	"flag"
	"reflect"
	"testing"

	"github.com/urfave/cli/v2"
)

// Validates that Flag implements the flag.Getter interface.
var _ flag.Getter = &Flag{}

// Validates that CliFlag implements the cli.Flag interface.
var _ cli.Flag = &CliFlag{}

func TestFlag(t *testing.T) {
	for _, tc := range []struct {
		name    string
		input   []string
		wantVal map[string]string
		wantErr bool
	}{
		{
			name:  "one value",
			input: []string{"--arg", "a=b"},
			wantVal: map[string]string{
				"a": "b",
			},
		},
		{
			name:  "multiple values",
			input: []string{"--arg", "a=b", "--arg", "c=d", "--arg", "e=f"},
			wantVal: map[string]string{
				"a": "b",
				"c": "d",
				"e": "f",
			},
		},
		{
			name:    "repeated value",
			input:   []string{"--arg", "a=b", "--arg", "a=d"},
			wantErr: true,
		},
		{
			name:    "not key equals value",
			input:   []string{"--arg", "ab"},
			wantErr: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := Flag{
				Values: map[string]string{},
			}
			var set flag.FlagSet
			set.Func("arg", "", func(s string) error {
				return f.Set(s)
			})
			err := set.Parse(tc.input)
			if tc.wantErr {
				if err == nil {
					t.Fatalf("Parse(%+v) err = nil, want = non-nil", tc.input)
				}
			} else {
				if err != nil {
					t.Fatalf("Parse(%+v) err = %+v, want = nil", tc.input, err)
				}
				if !reflect.DeepEqual(f.Values, tc.wantVal) {
					t.Fatalf("f.Values got = %+v, want = %+v", f.Values, tc.wantVal)
				}
			}
		})
	}
}
