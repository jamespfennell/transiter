package update

import (
	"context"
	"log"
)

func Run(ctx context.Context, systemId, feedId string) {
	log.Printf("Starting update for %s/%s\n", systemId, feedId)
}
