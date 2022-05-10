package session

import (
	"context"
	"path"
	"strings"

	"github.com/jamespfennell/transiter/internal/apihelpers"
	"google.golang.org/grpc/metadata"
)

type HrefGenerator struct {
	enabled bool
	baseUrl string
}

var xTransiterHostLower = strings.ToLower(apihelpers.XTransiterHost)

func NewHrefGenerator(ctx context.Context) HrefGenerator {
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if baseUrl, ok := md[xTransiterHostLower]; ok {
			return HrefGenerator{enabled: true, baseUrl: baseUrl[0]}
		}
	}
	return HrefGenerator{}
}

func (h HrefGenerator) Systems() *string {
	return h.generate("systems")
}

func (h HrefGenerator) System(system_id string) *string {
	return h.generate("systems", system_id)
}

func (h HrefGenerator) AgenciesInSystem(system_id string) *string {
	return h.generate("systems", system_id, "agencies")
}

func (h HrefGenerator) FeedsInSystem(system_id string) *string {
	return h.generate("systems", system_id, "feeds")
}

func (h HrefGenerator) RoutesInSystem(system_id string) *string {
	return h.generate("systems", system_id, "routes")
}

func (h HrefGenerator) StopsInSystem(system_id string) *string {
	return h.generate("systems", system_id, "stops")
}

func (h HrefGenerator) TransfersInSystem(system_id string) *string {
	return h.generate("systems", system_id, "transfers")
}

func (h HrefGenerator) Agency(system_id string, agency_id string) *string {
	return h.generate("systems", system_id, "agencies", agency_id)
}

func (h HrefGenerator) Feed(system_id string, feed_id string) *string {
	return h.generate("systems", system_id, "feeds", feed_id)
}

func (h HrefGenerator) FeedUpdates(system_id string, feed_id string) *string {
	return h.generate("systems", system_id, "feeds", feed_id, "updates")
}

func (h HrefGenerator) Route(system_id string, route_id string) *string {
	return h.generate("systems", system_id, "routes", route_id)
}

func (h HrefGenerator) Trip(system_id string, route_id string, trip_id string) *string {
	return h.generate("systems", system_id, "routes", route_id, "trips", trip_id)
}

func (h HrefGenerator) Stop(system_id string, stop_id string) *string {
	return h.generate("systems", system_id, "stops", stop_id)
}

func (h HrefGenerator) generate(elem ...string) *string {
	if !h.enabled {
		return nil
	}
	res := h.baseUrl + "/" + path.Join(elem...)
	return &res
}
