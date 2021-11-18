package util

import (
	"context"

	_ "github.com/lib/pq"
	"google.golang.org/grpc/metadata"
)

type HrefGenerator struct {
	enabled bool
	baseUrl string
}

func NewHrefGenerator(ctx context.Context) HrefGenerator {
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if baseUrl, ok := md["x-transiter-base-url"]; ok {
			return HrefGenerator{enabled: true, baseUrl: baseUrl[0]}
		}
	}
	return HrefGenerator{}
}

func (h HrefGenerator) Systems() string {
	if !h.enabled {
		return ""
	}
	return h.baseUrl + "/systems"
}
