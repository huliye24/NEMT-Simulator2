// Package datasource provides data source integrations for NEMT Gateway
package datasource

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/tencentyun/cos-go-sdk-v5"
)

// COSConfig holds Tencent Cloud COS configuration
type COSConfig struct {
	Enabled   bool
	SecretID  string
	SecretKey string
	Bucket    string
	Region    string
}

// COSDataSource provides market data from Tencent Cloud COS
type COSDataSource struct {
	client  *cos.Client
	bucket  string
	cache   *Cache
	cacheMu sync.RWMutex
}

// CacheEntry represents a cached item
type CacheEntry struct {
	Data     []byte
	ExpireAt time.Time
}

// Cache implements an in-memory cache with TTL
type Cache struct {
	items map[string]CacheEntry
	mu    sync.RWMutex
	ttl   time.Duration
}

// NewCache creates a new cache with the specified TTL
func NewCache(ttl time.Duration) *Cache {
	c := &Cache{
		items: make(map[string]CacheEntry),
		ttl:   ttl,
	}
	go c.cleanup()
	return c
}

// Get retrieves an item from cache
func (c *Cache) Get(key string) ([]byte, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if entry, ok := c.items[key]; ok && time.Now().Before(entry.ExpireAt) {
		return entry.Data, true
	}
	return nil, false
}

// Set stores an item in cache
func (c *Cache) Set(key string, data []byte) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.items[key] = CacheEntry{
		Data:     data,
		ExpireAt: time.Now().Add(c.ttl),
	}
}

// cleanup periodically removes expired items
func (c *Cache) cleanup() {
	ticker := time.NewTicker(c.ttl)
	defer ticker.Stop()

	for range ticker.C {
		c.mu.Lock()
		now := time.Now()
		for k, v := range c.items {
			if now.After(v.ExpireAt) {
				delete(c.items, k)
			}
		}
		c.mu.Unlock()
	}
}

// NewCOSDataSource creates a new COS data source
func NewCOSDataSource(cfg COSConfig) (*COSDataSource, error) {
	if !cfg.Enabled {
		return nil, fmt.Errorf("COS is not enabled")
	}

	if cfg.SecretID == "" || cfg.SecretKey == "" {
		return nil, fmt.Errorf("COS credentials are required")
	}

	u, err := url.Parse(fmt.Sprintf(
		"https://%s.cos.%s.myqcloud.com",
		cfg.Bucket, cfg.Region,
	))
	if err != nil {
		return nil, fmt.Errorf("invalid COS URL: %w", err)
	}

	b := &cos.BaseURL{BucketURL: u}
	client := cos.NewClient(b, &http.Client{
		Timeout: 10 * time.Second,
		Transport: &cos.AuthorizationTransport{
			SecretID:  cfg.SecretID,
			SecretKey: cfg.SecretKey,
		},
	})

	return &COSDataSource{
		client:  client,
		bucket:  cfg.Bucket,
		cache:   NewCache(5 * time.Minute), // 5 minute cache TTL
	}, nil
}

// GetKlines retrieves K-line data from COS
func (c *COSDataSource) GetKlines(ctx context.Context, symbol, interval string) ([]byte, error) {
	cacheKey := fmt.Sprintf("%s_%s", symbol, interval)

	// Check cache first
	c.cacheMu.RLock()
	if cached, ok := c.cache.Get(cacheKey); ok {
		c.cacheMu.RUnlock()
		return cached, nil
	}
	c.cacheMu.RUnlock()

	// Build the COS key
	key := fmt.Sprintf("market_data/binance/%s/%s/latest.json", symbol, interval)

	// Create context with timeout
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	// Get object from COS
	resp, err := c.client.Object.Get(ctx, key, nil)
	if err != nil {
		return nil, fmt.Errorf("COS get failed for %s: %w", key, err)
	}
	defer resp.Body.Close()

	// Read the response body
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Update cache
	c.cacheMu.Lock()
	c.cache.Set(cacheKey, data)
	c.cacheMu.Unlock()

	return data, nil
}

// GetIndex retrieves the index file from COS
func (c *COSDataSource) GetIndex(ctx context.Context) ([]byte, error) {
	cacheKey := "_index"

	// Check cache first
	c.cacheMu.RLock()
	if cached, ok := c.cache.Get(cacheKey); ok {
		c.cacheMu.RUnlock()
		return cached, nil
	}
	c.cacheMu.RUnlock()

	// Build the COS key
	key := "market_data/binance/_index.json"

	// Create context with timeout
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	// Get object from COS
	resp, err := c.client.Object.Get(ctx, key, nil)
	if err != nil {
		return nil, fmt.Errorf("COS get failed for %s: %w", key, err)
	}
	defer resp.Body.Close()

	// Read the response body
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Update cache
	c.cacheMu.Lock()
	c.cache.Set(cacheKey, data)
	c.cacheMu.Unlock()

	return data, nil
}

// InvalidateCache clears the cache for a specific symbol or all
func (c *COSDataSource) InvalidateCache(symbol ...string) {
	c.cacheMu.Lock()
	defer c.cacheMu.Unlock()

	if len(symbol) == 0 {
		// Clear all
		c.cache = NewCache(5 * time.Minute)
		return
	}

	// Clear specific symbols
	for _, s := range symbol {
		for _, tf := range []string{"1m", "5m", "15m", "1h", "4h", "1d"} {
			key := fmt.Sprintf("%s_%s", s, tf)
			delete(c.cache.items, key)
		}
	}
}

// HealthCheck performs a health check on COS connectivity
func (c *COSDataSource) HealthCheck(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	// Try to get the index file as health check
	_, err := c.client.Object.Get(ctx, "market_data/binance/_index.json", nil)
	if err != nil {
		return fmt.Errorf("COS health check failed: %w", err)
	}

	return nil
}
