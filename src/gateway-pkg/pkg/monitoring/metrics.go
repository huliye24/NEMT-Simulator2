// Package monitoring provides Prometheus metrics and monitoring
package monitoring

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// ============================================================================
// Metrics
// ============================================================================

// Metrics holds all Prometheus metrics
type Metrics struct {
	// HTTP metrics
	HTTPRequestsTotal   *prometheus.CounterVec
	HTTPRequestDuration *prometheus.HistogramVec
	HTTPRequestsInFlight prometheus.Gauge

	// Business metrics
	StrategiesTotal     prometheus.Gauge
	StrategiesActive    prometheus.Gauge
	CapsulesTotal      prometheus.Gauge
	BacktestsTotal     prometheus.Counter
	BacktestsRunning   prometheus.Gauge
	SimulationsTotal   prometheus.Counter
	SimulationsRunning prometheus.Gauge

	// Market data metrics
	MarketDataReceived prometheus.Counter
	MarketDataErrors  prometheus.Counter
	WebSocketSessions prometheus.Gauge

	// Performance metrics
	LatencyTotal   prometheus.Histogram
	LatencyGateway prometheus.Histogram

	// System metrics
	MemoryUsage prometheus.Gauge
	CPUUsage    prometheus.Gauge
	GoRoutines prometheus.Gauge
}

// NewMetrics creates and registers all metrics
func NewMetrics(namespace string) *Metrics {
	m := &Metrics{
		// HTTP
		HTTPRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "http_requests_total",
				Help:      "Total number of HTTP requests",
			},
			[]string{"method", "endpoint", "status"},
		),

		HTTPRequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "http_request_duration_seconds",
				Help:      "HTTP request duration in seconds",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"method", "endpoint"},
		),

		HTTPRequestsInFlight: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "http_requests_in_flight",
				Help:      "Number of HTTP requests currently being processed",
			},
		),

		// Business
		StrategiesTotal: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "strategies_total",
				Help:      "Total number of strategies",
			},
		),

		StrategiesActive: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "strategies_active",
				Help:      "Number of active strategies",
			},
		),

		CapsulesTotal: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "capsules_total",
				Help:      "Total number of capsules",
			},
		),

		BacktestsTotal: promauto.NewCounter(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "backtests_total",
				Help:      "Total number of backtests run",
			},
		),

		BacktestsRunning: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "backtests_running",
				Help:      "Number of backtests currently running",
			},
		),

		SimulationsTotal: promauto.NewCounter(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "simulations_total",
				Help:      "Total number of simulations run",
			},
		),

		SimulationsRunning: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "simulations_running",
				Help:      "Number of simulations currently running",
			},
		),

		// Market data
		MarketDataReceived: promauto.NewCounter(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "market_data_received_total",
				Help:      "Total number of market data messages received",
			},
		),

		MarketDataErrors: promauto.NewCounter(
			prometheus.CounterOpts{
				Namespace: namespace,
				Name:      "market_data_errors_total",
				Help:      "Total number of market data errors",
			},
		),

		WebSocketSessions: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "websocket_sessions_total",
				Help:      "Number of active WebSocket sessions",
			},
		),

		// Performance
		LatencyTotal: promauto.NewHistogram(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "latency_total_seconds",
				Help:      "Total processing latency in seconds",
				Buckets:   []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1},
			},
		),

		LatencyGateway: promauto.NewHistogram(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Name:      "latency_gateway_seconds",
				Help:      "Gateway processing latency in seconds",
				Buckets:   prometheus.DefBuckets,
			},
		),

		// System
		MemoryUsage: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "memory_usage_bytes",
				Help:      "Current memory usage in bytes",
			},
		),

		CPUUsage: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "cpu_usage_percent",
				Help:      "Current CPU usage percentage",
			},
		),

		GoRoutines: promauto.NewGauge(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Name:      "goroutines",
				Help:      "Number of Go routines",
			},
		),
	}

	return m
}

// ============================================================================
// Record Methods
// ============================================================================

// RecordHTTPRequest records an HTTP request
func (m *Metrics) RecordHTTPRequest(method, endpoint, status string) {
	m.HTTPRequestsTotal.WithLabelValues(method, endpoint, status).Inc()
}

// RecordHTTPDuration records HTTP request duration
func (m *Metrics) RecordHTTPDuration(method, endpoint string, seconds float64) {
	m.HTTPRequestDuration.WithLabelValues(method, endpoint).Observe(seconds)
}

// IncrementWebSocketSessions increments WebSocket session count
func (m *Metrics) IncrementWebSocketSessions() {
	m.WebSocketSessions.Inc()
}

// DecrementWebSocketSessions decrements WebSocket session count
func (m *Metrics) DecrementWebSocketSessions() {
	m.WebSocketSessions.Dec()
}

// RecordMarketData records market data received
func (m *Metrics) RecordMarketData() {
	m.MarketDataReceived.Inc()
}

// RecordMarketDataError records a market data error
func (m *Metrics) RecordMarketDataError() {
	m.MarketDataErrors.Inc()
}

// UpdateSystemMetrics updates system-level metrics
func (m *Metrics) UpdateSystemMetrics() {
	// These would be populated by actual system monitoring
	m.GoRoutines.Set(float64(0)) // runtime.NumGoroutine()
}
