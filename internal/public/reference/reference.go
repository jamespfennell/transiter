// Package reference contains constructors for public API reference types.
package reference

import (
	"context"
	"path"
	"strings"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"google.golang.org/grpc/metadata"
)

// Generator is used for generating reference messages.
type Generator struct {
	urlEnabled bool
	baseURL    string
	systems    map[string]*api.System_Reference
}

// XTransiterHost is the key of the HTTP header whose value is used as the base URL in all link values.
//
// TODO(APIv2): rename X-Transiter-BaseURL
const XTransiterHost = "X-Transiter-Host"

var xTransiterHostLower = strings.ToLower(XTransiterHost)

func NewGenerator(ctx context.Context) Generator {
	var urlEnabled bool
	var baseURL string
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if hdrVal, ok := md[xTransiterHostLower]; ok {
			urlEnabled = true
			baseURL = hdrVal[0]
		}
	}
	return Generator{
		urlEnabled: urlEnabled,
		baseURL:    baseURL,
		systems:    map[string]*api.System_Reference{},
	}
}

func (h Generator) SystemsChildResources(count int) *api.ChildResources {
	return h.generateChildResources(int64(count), "systems")
}

func (h Generator) System(id string) *api.System_Reference {
	if _, ok := h.systems[id]; !ok {
		h.systems[id] = &api.System_Reference{
			Id:       id,
			Resource: h.generateResource("systems", id),
		}
	}
	return h.systems[id]
}

func (h Generator) AgenciesChildResources(systemID string, count int64) *api.ChildResources {
	return h.generateChildResources(count, "systems", systemID, "agencies")
}

func (h Generator) Agency(id string, systemID string, name string) *api.Agency_Reference {
	return &api.Agency_Reference{
		Id:       id,
		System:   h.System(systemID),
		Name:     name,
		Resource: h.generateResource("systems", systemID, "agencies", id),
	}
}

func (h Generator) Alert(id, systemID, cause, effect string) *api.Alert_Reference {
	return &api.Alert_Reference{
		Id:       id,
		System:   h.System(systemID),
		Cause:    convert.AlertCause(cause),
		Effect:   convert.AlertEffect(effect),
		Resource: h.generateResource("systems", systemID, "alerts", id),
	}
}

func (h Generator) FeedsChildResources(systemID string, count int64) *api.ChildResources {
	return h.generateChildResources(count, "systems", systemID, "feeds")
}

func (h Generator) Feed(id string, systemID string) *api.Feed_Reference {
	return &api.Feed_Reference{
		Id:       id,
		System:   h.System(systemID),
		Resource: h.generateResource("systems", systemID, "feeds", id),
	}
}

func (h Generator) RoutesChildResources(systemID string, count int64) *api.ChildResources {
	return h.generateChildResources(count, "systems", systemID, "routes")
}

func (h Generator) Route(id string, systemID string, color string) *api.Route_Reference {
	return &api.Route_Reference{
		Id:       id,
		System:   h.System(systemID),
		Color:    color,
		Resource: h.generateResource("systems", systemID, "routes", id),
	}
}

func (h Generator) Trip(id string, route *api.Route_Reference, destination *api.Stop_Reference, vehicle *api.Vehicle_Reference, directionID bool) *api.Trip_Reference {
	return &api.Trip_Reference{
		Id:          id,
		Route:       route,
		Destination: destination,
		Vehicle:     vehicle,
		DirectionId: directionID,
		Resource:    h.generateResource("systems", route.System.Id, "routes", route.Id, "trips", id),
	}
}

func (h Generator) StopsChildResources(systemID string, count int64) *api.ChildResources {
	return h.generateChildResources(count, "systems", systemID, "stops")
}

func (h Generator) Stop(id string, systemID string, name pgtype.Text) *api.Stop_Reference {
	return &api.Stop_Reference{
		Id:       id,
		System:   h.System(systemID),
		Name:     convert.SQLNullString(name),
		Resource: h.generateResource("systems", systemID, "stops", id),
	}
}

func (h Generator) TransfersChildResources(systemID string, count int64) *api.ChildResources {
	return h.generateChildResources(count, "systems", systemID, "transfers")
}

func (h Generator) Vehicle(id string, systemID string) *api.Vehicle_Reference {
	return &api.Vehicle_Reference{
		Id:       id,
		Resource: h.generateResource("systems", systemID, "vehicles", id),
	}
}

func (h Generator) Shape(id string, systemID string) *api.Shape_Reference {
	return &api.Shape_Reference{
		Id:       id,
		Resource: h.generateResource("systems", systemID, "shapes", id),
	}
}

func (h Generator) generateResource(elem ...string) *api.Resource {
	return &api.Resource{
		Path: path.Join(elem...),
		Url:  h.generateURL(elem...),
	}
}

func (h Generator) generateChildResources(count int64, elem ...string) *api.ChildResources {
	return &api.ChildResources{
		Count: count,
		Path:  path.Join(elem...),
		Url:   h.generateURL(elem...),
	}
}

func (h Generator) generateURL(elem ...string) *string {
	if !h.urlEnabled {
		return nil
	}
	res := h.baseURL + "/" + path.Join(elem...)
	return &res
}
