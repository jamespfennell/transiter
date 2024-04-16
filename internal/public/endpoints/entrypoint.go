// Package endpoints contains the logic for each public API endpoint.
package endpoints

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/version"
)

func Entrypoint(ctx context.Context, r *Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	systemIDs, err := r.Querier.ListSystems(ctx)
	if err != nil {
		return nil, err
	}
	var systems []*api.System_Reference
	for _, system := range systemIDs {
		systems = append(systems, r.Reference.System(system.ID))
	}
	return &api.EntrypointReply{
		Transiter: &api.EntrypointReply_TransiterDetails{
			Version: version.Version(),
			Href:    "https://github.com/jamespfennell/transiter",
			// TODO: build information
		},
		Systems: &api.ChildResources{
			Count: int64(len(systems)),
			Href:  r.Reference.SystemsHref(),
		},
	}, nil
}
