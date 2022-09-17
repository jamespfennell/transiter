// Package reference contains constructors for public API reference types.
package reference

import (
	"context"
	"database/sql"
	"path"
	"strings"

	"github.com/jamespfennell/transiter/internal/convert"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"google.golang.org/grpc/metadata"
)

// Generator is used for generating reference messages.
type Generator struct {
	hrefEnabled bool
	baseURL     string
	systems     map[string]*api.System_Reference
}

// XTransiterHost is the key of the HTTP header whose value is used as the base URL in all link values.
//
// TODO(APIv2): rename X-Transiter-BaseURL
const XTransiterHost = "X-Transiter-Host"

var xTransiterHostLower = strings.ToLower(XTransiterHost)

func NewGenerator(ctx context.Context) Generator {
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if baseURL, ok := md[xTransiterHostLower]; ok {
			return Generator{hrefEnabled: true, baseURL: baseURL[0]}
		}
	}
	return Generator{
		systems: map[string]*api.System_Reference{},
	}
}

func (h Generator) SystemsHref() *string {
	return h.generateHref("systems")
}

func (h Generator) System(id string) *api.System_Reference {
	if _, ok := h.systems[id]; !ok {
		h.systems[id] = &api.System_Reference{
			Id:   id,
			Href: h.generateHref("systems", id),
		}
	}
	return h.systems[id]
}

func (h Generator) AgenciesHref(systemID string) *string {
	return h.generateHref("systems", systemID, "agencies")
}

func (h Generator) Agency(id string, systemID string, name string) *api.Agency_Reference {
	return &api.Agency_Reference{
		Id:     id,
		System: h.System(systemID),
		Name:   name,
		Href:   h.generateHref("systems", systemID, "agencies", id),
	}
}

func (h Generator) Alert(id, systemID, cause, effect string) *api.Alert_Reference {
	return &api.Alert_Reference{
		Id:     id,
		System: h.System(systemID),
		Cause:  convert.AlertCause(cause),
		Effect: convert.AlertEffect(effect),
		Href:   h.generateHref("systems", systemID, "alerts", id),
	}
}

func (h Generator) FeedsHref(systemID string) *string {
	return h.generateHref("systems", systemID, "feeds")
}

func (h Generator) Feed(id string, systemID string) *api.Feed_Reference {
	return &api.Feed_Reference{
		Id:     id,
		System: h.System(systemID),
		Href:   h.generateHref("systems", systemID, "feeds", id),
	}
}

func (h Generator) FeedUpdatesHref(systemID string, feedID string) *string {
	return h.generateHref("systems", systemID, "feeds", feedID, "updates")
}

func (h Generator) RoutesHref(systemID string) *string {
	return h.generateHref("systems", systemID, "routes")
}

func (h Generator) Route(id string, systemID string, color string) *api.Route_Reference {
	return &api.Route_Reference{
		Id:     id,
		System: h.System(systemID),
		Color:  color,
		Href:   h.generateHref("systems", systemID, "routes", id),
	}
}

func (h Generator) Trip(id string, route *api.Route_Reference, destination *api.Stop_Reference, vehicle *api.Vehicle_Reference) *api.Trip_Reference {
	return &api.Trip_Reference{
		Id:          id,
		Route:       route,
		Destination: destination,
		Vehicle:     vehicle,
		Href:        h.generateHref("systems", route.System.Id, "routes", route.Id, "trips", id),
	}
}

func (h Generator) StopsHref(systemID string) *string {
	return h.generateHref("systems", systemID, "stops")
}

func (h Generator) Stop(id string, systemID string, name sql.NullString) *api.Stop_Reference {
	return &api.Stop_Reference{
		Id:     id,
		System: h.System(systemID),
		Name:   convert.SQLNullString(name),
		Href:   h.generateHref("systems", systemID, "stops", id),
	}
}

func (h Generator) TransfersHref(systemID string) *string {
	return h.generateHref("systems", systemID, "transfers")
}

func (h Generator) Vehicle(id string) *api.Vehicle_Reference {
	// TODO: vehicle
	return &api.Vehicle_Reference{
		Id: id,
	}
}

func (h Generator) generateHref(elem ...string) *string {
	if !h.hrefEnabled {
		return nil
	}
	res := h.baseURL + "/" + path.Join(elem...)
	return &res
}
