// Package href contains a facility for generating links to entities in the REST API.
package href

import (
	"context"
	"path"
	"strings"

	"google.golang.org/grpc/metadata"
)

type Generator struct {
	enabled bool
	baseURL string
}

// XTransiterHost is the key of the HTTP header whose value is used as the base URL in all link values.
//
// TODO(APIv2): rename X-Transiter-BaseURL
const XTransiterHost = "X-Transiter-Host"

var xTransiterHostLower = strings.ToLower(XTransiterHost)

func NewGenerator(ctx context.Context) Generator {
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if baseURL, ok := md[xTransiterHostLower]; ok {
			return Generator{enabled: true, baseURL: baseURL[0]}
		}
	}
	return Generator{}
}

func (h Generator) Systems() *string {
	return h.generate("systems")
}

func (h Generator) System(systemID string) *string {
	return h.generate("systems", systemID)
}

func (h Generator) AgenciesInSystem(systemID string) *string {
	return h.generate("systems", systemID, "agencies")
}

func (h Generator) FeedsInSystem(systemID string) *string {
	return h.generate("systems", systemID, "feeds")
}

func (h Generator) RoutesInSystem(systemID string) *string {
	return h.generate("systems", systemID, "routes")
}

func (h Generator) StopsInSystem(systemID string) *string {
	return h.generate("systems", systemID, "stops")
}

func (h Generator) TransfersInSystem(systemID string) *string {
	return h.generate("systems", systemID, "transfers")
}

func (h Generator) Agency(systemID string, agencyID string) *string {
	return h.generate("systems", systemID, "agencies", agencyID)
}

func (h Generator) Feed(systemID string, feedID string) *string {
	return h.generate("systems", systemID, "feeds", feedID)
}

func (h Generator) FeedUpdates(systemID string, feedID string) *string {
	return h.generate("systems", systemID, "feeds", feedID, "updates")
}

func (h Generator) Route(systemID string, routeID string) *string {
	return h.generate("systems", systemID, "routes", routeID)
}

func (h Generator) Trip(systemID string, routeID string, tripID string) *string {
	return h.generate("systems", systemID, "routes", routeID, "trips", tripID)
}

func (h Generator) Stop(systemID string, stopID string) *string {
	return h.generate("systems", systemID, "stops", stopID)
}

func (h Generator) generate(elem ...string) *string {
	if !h.enabled {
		return nil
	}
	res := h.baseURL + "/" + path.Join(elem...)
	return &res
}
