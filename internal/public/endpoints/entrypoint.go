// Package endpoints contains the logic for each public API endpoint.
package endpoints

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
)

func Entrypoint(ctx context.Context, r *Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	numSystems, err := r.Querier.CountSystems(ctx)
	if err != nil {
		return nil, err
	}
	return &api.EntrypointReply{
		Transiter: &api.EntrypointReply_TransiterDetails{
			Version: "1.0.0alpha",
			Href:    "https://github.com/jamespfennell/transiter",
		},
		Systems: &api.CountAndHref{
			Count: numSystems,
			Href:  r.Href.Systems(),
		},
	}, nil
}
