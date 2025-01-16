// Package endpoints contains the logic for each public API endpoint.
package endpoints

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/version"
)

func Entrypoint(ctx context.Context, r *Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	systems, err := r.Querier.ListSystems(ctx)
	if err != nil {
		return nil, err
	}
	return &api.EntrypointReply{
		Transiter: &api.EntrypointReply_TransiterDetails{
			Version: version.Version(),
			Url:     "https://github.com/jamespfennell/transiter",
		},
		Systems: r.Reference.SystemsChildResources(len(systems)),
	}, nil
}
