package href

import (
	"context"
	"path"
	"strings"

	"google.golang.org/grpc/metadata"
)

type Generator struct {
	enabled bool
	baseUrl string
}

// TODO(APIv2): rename X-Transiter-BaseURL
const XTransiterHost = "X-Transiter-Host"

var xTransiterHostLower = strings.ToLower(XTransiterHost)

func NewGenerator(ctx context.Context) Generator {
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if baseUrl, ok := md[xTransiterHostLower]; ok {
			return Generator{enabled: true, baseUrl: baseUrl[0]}
		}
	}
	return Generator{}
}

func (h Generator) Systems() *string {
	return h.generate("systems")
}

func (h Generator) System(system_id string) *string {
	return h.generate("systems", system_id)
}

func (h Generator) AgenciesInSystem(system_id string) *string {
	return h.generate("systems", system_id, "agencies")
}

func (h Generator) FeedsInSystem(system_id string) *string {
	return h.generate("systems", system_id, "feeds")
}

func (h Generator) RoutesInSystem(system_id string) *string {
	return h.generate("systems", system_id, "routes")
}

func (h Generator) StopsInSystem(system_id string) *string {
	return h.generate("systems", system_id, "stops")
}

func (h Generator) TransfersInSystem(system_id string) *string {
	return h.generate("systems", system_id, "transfers")
}

func (h Generator) Agency(system_id string, agency_id string) *string {
	return h.generate("systems", system_id, "agencies", agency_id)
}

func (h Generator) Feed(system_id string, feed_id string) *string {
	return h.generate("systems", system_id, "feeds", feed_id)
}

func (h Generator) FeedUpdates(system_id string, feed_id string) *string {
	return h.generate("systems", system_id, "feeds", feed_id, "updates")
}

func (h Generator) Route(system_id string, route_id string) *string {
	return h.generate("systems", system_id, "routes", route_id)
}

func (h Generator) Trip(system_id string, route_id string, trip_id string) *string {
	return h.generate("systems", system_id, "routes", route_id, "trips", trip_id)
}

func (h Generator) Stop(system_id string, stop_id string) *string {
	return h.generate("systems", system_id, "stops", stop_id)
}

func (h Generator) generate(elem ...string) *string {
	if !h.enabled {
		return nil
	}
	res := h.baseUrl + "/" + path.Join(elem...)
	return &res
}
