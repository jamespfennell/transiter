package reference

import (
	"context"
	"fmt"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"google.golang.org/grpc/metadata"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/testing/protocmp"
)

const (
	systemID = "systemID"
)

func TestGenerator(t *testing.T) {

	for _, tc := range []struct {
		name    string
		headers map[string]string
		want    any
		builder func(g Generator) any
	}{
		{
			name:    "system, no headers",
			headers: nil,
			want: &api.System_Reference{
				Id: systemID,
				Resource: &api.Resource{
					Path: fmt.Sprintf("systems/%s", systemID),
				},
			},
			builder: func(g Generator) any {
				return g.System(systemID)
			},
		},
		{
			name: "system, headers",
			headers: map[string]string{
				XTransiterHost: "https://demo.transiter.dev",
			},
			want: &api.System_Reference{
				Id: systemID,
				Resource: &api.Resource{
					Path: fmt.Sprintf("systems/%s", systemID),
					Url:  proto.String(fmt.Sprintf("https://demo.transiter.dev/systems/%s", systemID)),
				},
			},
			builder: func(g Generator) any {
				return g.System(systemID)
			},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			ctx := metadata.NewIncomingContext(context.Background(), metadata.New(tc.headers))
			g := NewGenerator(ctx)
			got := tc.builder(g)
			if diff := cmp.Diff(tc.want, got, protocmp.Transform()); diff != "" {
				t.Errorf("got=%+v, want=%+v, diff=%s", got, tc.want, diff)
			}
		})
	}
}
