// Package monitoring contains methods for recording metrics and reporting them through a HTTP handler
package monitoring

import (
	"fmt"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var feedUpdateCount = promauto.NewCounterVec(
	prometheus.CounterOpts{
		Name: "transiter_feed_update_count",
		Help: "Number of completed feed updates",
	},
	[]string{"system_id", "feed_id", "status", "result"},
)
var feedUpdateLatency = promauto.NewHistogramVec(
	prometheus.HistogramOpts{
		Name:    "transiter_feed_update_latency",
		Help:    "Time taken to complete a feed update in seconds",
		Buckets: []float64{0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.1, 1.4},
	},
	[]string{"system_id", "feed_id", "status", "result"},
)
var publicRequestCount = promauto.NewCounterVec(
	prometheus.CounterOpts{
		Name: "transiter_public_request_count",
		Help: "Number of requests to the public service (HTTP and gRPC)",
	},
	[]string{"method_name", "is_error"},
)
var publicRequestLatency = promauto.NewHistogramVec(
	prometheus.HistogramOpts{
		Name:    "transiter_public_request_latency",
		Help:    "Latency in seconds of requests to the public service (HTTP and gRPC)",
		Buckets: prometheus.DefBuckets,
	},
	[]string{"method_name", "is_error"},
)

func RecordFeedUpdate(systemID, feedID, status, result string, duration time.Duration) {
	feedUpdateCount.WithLabelValues(systemID, feedID, status, result).Inc()
	feedUpdateLatency.WithLabelValues(systemID, feedID, status, result).Observe(duration.Seconds())
}

func RecordPublicRequest(methodName string, err error, duration time.Duration) {
	errString := fmt.Sprintf("%t", err != nil)
	publicRequestCount.WithLabelValues(methodName, errString).Inc()
	publicRequestLatency.WithLabelValues(methodName, errString).Observe(duration.Seconds())
}

func Handler() http.Handler {
	return promhttp.Handler()
}
