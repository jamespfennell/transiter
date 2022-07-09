// Package endpoints contains the logic for each public API endpoint.
package endpoints

import (
	"context"

	"github.com/jamespfennell/transiter/internal/gen/api"
)

func Entrypoint(ctx context.Context, r *Context, req *api.EntrypointRequest) (*api.EntrypointReply, error) {
	systemIDs, err := r.Querier.ListSystemIDs(ctx)
	if err != nil {
		return nil, err
	}
	var systems []*api.System_Preview
	for _, id := range systemIDs {
		systems = append(systems, &api.System_Preview{
			Id:   id,
			Href: r.Href.System(id),
		})
	}
	return &api.EntrypointReply{
		Transiter: &api.EntrypointReply_TransiterDetails{
			Version: "1.0.0alpha",
			Href:    "https://github.com/jamespfennell/transiter",
		},
		Systems: systems,
	}, nil
}