// Package middleware provides HTTP middleware for NEMT Gateway
package middleware

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
)

// RequestID adds a unique request ID to each request
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = common.GenerateRequestID()
		}
		c.Set("request_id", requestID)
		c.Header("X-Request-ID", requestID)
		c.Next()
	}
}

// Logger logs HTTP requests
func Logger(log *logger.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()

		fields := map[string]interface{}{
			"status":    status,
			"method":    c.Request.Method,
			"path":      path,
			"query":     query,
			"ip":        c.ClientIP(),
			"latency":   latency.String(),
			"user_agent": c.Request.UserAgent(),
		}

		if requestID, exists := c.Get("request_id"); exists {
			fields["request_id"] = requestID
		}

		switch {
		case status >= 500:
			log.Error("Server error", nil, fields)
		case status >= 400:
			log.Warn("Client error", fields)
		default:
			log.Info("Request completed", fields)
		}
	}
}

// Recovery recovers from panics
func Recovery(log *logger.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				fields := map[string]interface{}{
					"panic": err,
					"path":  c.Request.URL.Path,
				}
				log.Error("Panic recovered", nil, fields)
				c.AbortWithStatusJSON(500, common.NewErrorResponse("INTERNAL_ERROR", "Internal server error"))
			}
		}()
		c.Next()
	}
}

// CORS adds CORS headers
func CORS() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Accept, Authorization, X-Request-ID")
		c.Header("Access-Control-Max-Age", "86400")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}

// RateLimiter provides simple in-memory rate limiting
type RateLimiter struct {
	visitors map[string]*visitor
	mu       sync.RWMutex
	rate     int           // requests per window
	window   time.Duration // time window
}

type visitor struct {
	count    int
	lastSeen time.Time
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(rate int, window time.Duration) *RateLimiter {
	rl := &RateLimiter{
		visitors: make(map[string]*visitor),
		rate:     rate,
		window:   window,
	}

	// Start cleanup goroutine
	go rl.cleanup()

	return rl
}

// Allow checks if a request is allowed
func (rl *RateLimiter) Allow(ip string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	v, exists := rl.visitors[ip]
	if !exists {
		rl.visitors[ip] = &visitor{count: 1, lastSeen: time.Now()}
		return true
	}

	if time.Since(v.lastSeen) > rl.window {
		v.count = 1
		v.lastSeen = time.Now()
		return true
	}

	if v.count >= rl.rate {
		return false
	}

	v.count++
	v.lastSeen = time.Now()
	return true
}

// cleanup removes old visitors
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(time.Minute)
	for range ticker.C {
		rl.mu.Lock()
		for ip, v := range rl.visitors {
			if time.Since(v.lastSeen) > rl.window*2 {
				delete(rl.visitors, ip)
			}
		}
		rl.mu.Unlock()
	}
}

// RateLimit returns a rate limiting middleware
func RateLimit(rate int, window time.Duration) gin.HandlerFunc {
	limiter := NewRateLimiter(rate, window)

	return func(c *gin.Context) {
		ip := c.ClientIP()
		if !limiter.Allow(ip) {
			c.JSON(http.StatusTooManyRequests, common.NewErrorResponse("RATE_LIMITED", "Too many requests"))
			c.Abort()
			return
		}
		c.Next()
	}
}

// Auth provides authentication middleware (placeholder)
func Auth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// TODO: Implement proper authentication
		// For now, check for Authorization header
		auth := c.GetHeader("Authorization")
		if auth == "" {
			// Allow unauthenticated access for development
			c.Set("user_id", "anonymous")
		} else {
			// TODO: Validate JWT token
			c.Set("user_id", "authenticated")
		}
		c.Next()
	}
}

// Timeout adds a timeout to the request context
func Timeout(timeout time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Note: Gin doesn't support context timeout directly
		// This is a placeholder for future implementation
		c.Next()
	}
}

// Metrics provides metrics collection (placeholder)
type Metrics struct {
	requests    map[string]int
	durations   map[string][]time.Duration
	mu          sync.RWMutex
}

func NewMetrics() *Metrics {
	return &Metrics{
		requests:  make(map[string]int),
		durations: make(map[string][]time.Duration),
	}
}

func (m *Metrics) Record(path, method string, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	key := method + ":" + path
	m.requests[key]++
	m.durations[key] = append(m.durations[key], duration)
}

func (m *Metrics) GetStats() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stats := make(map[string]interface{})
	for key, count := range m.requests {
		stats[key+":count"] = count
	}
	return stats
}

// MetricsMiddleware returns a metrics middleware
func MetricsMiddleware(m *Metrics) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method

		c.Next()

		duration := time.Since(start)
		m.Record(path, method, duration)
	}
}
