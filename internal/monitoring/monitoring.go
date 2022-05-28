// Package monitoring contains methods for recording metrics and reporting them through a HTTP handler
package monitoring

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var feedUpdates = promauto.NewCounterVec(
	prometheus.CounterOpts{
		Name: "transiter_feed_updates",
		Help: "Completed feed updates by feed and result",
	},
	[]string{"system_id", "feed_id", "status", "result"},
)

func RecordFeedUpdate(systemID, feedID, status, result string) {
	feedUpdates.WithLabelValues(systemID, feedID, status, result).Inc()
}

func Handler() http.Handler {
	return promhttp.Handler()
}
