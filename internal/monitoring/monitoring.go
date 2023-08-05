// Package monitoring contains methods for recording metrics and reporting them through a HTTP handler
package monitoring

import (
	"fmt"
	"net/http"
	"time"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type Monitoring interface {
	RecordFeedUpdate(systemID, feedID string, feedUpdate *api.FeedUpdate)
	RecordPublicRequest(methodName string, err error, duration time.Duration)
	Handler() http.Handler
}

func NewPrometheusMonitoring(namespace string) Monitoring {
	registry := prometheus.NewRegistry()
	factory := promauto.With(registry)
	return &prometheusMonitoring{
		registry: registry,
		feedUpdateDownloadCount: factory.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "feed_update_download_count",
				Help:      "Number of feed downloads performed, partitioned by HTTP response code",
			},
			[]string{"system_id", "feed_id", "feed_type", "http_response_code"},
		),
		feedUpdateDownloadLatency: factory.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "feed_update_download_latency",
				Help:      "Latency of successfully downloading the feed data, in seconds",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"system_id", "feed_id", "feed_type"},
		),
		feedUpdateDownloadSize: factory.NewGaugeVec(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "feed_update_download_size",
				Help:      "Size of the feed data that was successfully downloaded, in bytes",
			},
			[]string{"system_id", "feed_id", "feed_type"},
		),
		feedUpdateDatabaseLatency: factory.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "feed_update_database_latency",
				Help:      "Latency of updating Postgres with the new feed data, in seconds",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"system_id", "feed_id", "feed_type"},
		),
		feedUpdateSuccessLatency: factory.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "feed_update_success_latency",
				Help:      "Total latency of updating a feed, in seconds",
				Buckets:   []float64{0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.1, 1.4},
			},
			[]string{"system_id", "feed_id", "feed_type"},
		),
		feedUpdateCount: factory.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "feed_update_count",
				Help:      "Number of feed updates performed, partitioned by the feed update status",
			},
			[]string{"system_id", "feed_id", "feed_type", "status"},
		),
		feedUpdateLastCompleted: factory.NewGaugeVec(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "feed_update_last_completed",
				Help:      "Unix milliseconds timestamp of when the most recent feed update completed",
			},
			[]string{"system_id", "feed_id", "feed_type", "result"},
		),
		publicRequestLatency: factory.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "public_request_latency",
				Help:      "Latency of requests to the public service (HTTP and gRPC), in seconds",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"method_name", "response_status"},
		),
	}
}

type prometheusMonitoring struct {
	registry                  *prometheus.Registry
	feedUpdateDownloadCount   *prometheus.CounterVec
	feedUpdateDownloadLatency *prometheus.HistogramVec
	feedUpdateDownloadSize    *prometheus.GaugeVec
	feedUpdateSuccessLatency  *prometheus.HistogramVec
	feedUpdateDatabaseLatency *prometheus.HistogramVec
	feedUpdateCount           *prometheus.CounterVec
	feedUpdateLastCompleted   *prometheus.GaugeVec
	publicRequestLatency      *prometheus.HistogramVec
}

func (m *prometheusMonitoring) RecordFeedUpdate(systemID, feedID string, feedUpdate *api.FeedUpdate) {
	var result string
	switch feedUpdate.Status {
	case api.FeedUpdate_SKIPPED:
		result = "SKIPPED"
	case api.FeedUpdate_UPDATED:
		result = "SUCCESS"
	default:
		result = "FAILED"
	}
	var feedType string
	if feedUpdate.FeedConfig != nil {
		feedType = feedUpdate.FeedConfig.GetType()
	} else {
		feedType = "UNKNOWN"
	}
	m.feedUpdateCount.WithLabelValues(systemID, feedID, feedType, feedUpdate.Status.String()).Inc()
	m.feedUpdateLastCompleted.WithLabelValues(systemID, feedID, feedType, result).Set(float64(time.Now().UnixMilli()))
	if feedUpdate.DownloadHttpStatusCode != nil {
		m.feedUpdateDownloadCount.WithLabelValues(systemID, feedID, feedType, fmt.Sprintf("%d", *feedUpdate.DownloadHttpStatusCode)).Inc()
	}
	if feedUpdate.DownloadLatencyMs != nil {
		m.feedUpdateDownloadLatency.WithLabelValues(systemID, feedID, feedType).Observe(float64(*feedUpdate.DownloadLatencyMs) / 1000)
	}
	if feedUpdate.ContentLength != nil {
		m.feedUpdateDownloadSize.WithLabelValues(systemID, feedID, feedType).Set(float64(*feedUpdate.ContentLength))
	}
	if feedUpdate.DatabaseLatencyMs != nil {
		m.feedUpdateDatabaseLatency.WithLabelValues(systemID, feedID, feedType).Observe(float64(*feedUpdate.DatabaseLatencyMs) / 1000)
	}
	if feedUpdate.Status == api.FeedUpdate_UPDATED {
		m.feedUpdateSuccessLatency.WithLabelValues(systemID, feedID, feedType).Observe(float64(feedUpdate.GetTotalLatencyMs()) / 1000)
	}
}

func (m *prometheusMonitoring) RecordPublicRequest(methodName string, err error, duration time.Duration) {
	responseStatus := errors.GetStatusCode(err).String()
	m.publicRequestLatency.WithLabelValues(methodName, responseStatus).Observe(duration.Seconds())
}

func (m *prometheusMonitoring) Handler() http.Handler {
	return promhttp.InstrumentMetricHandler(m.registry, promhttp.HandlerFor(m.registry, promhttp.HandlerOpts{}))
}
