// Package cache provides in-memory caching for NEMT Gateway
package cache

import (
	"container/list"
	"context"
	"sync"
	"time"
)

// Cache is a thread-safe LRU cache
type Cache struct {
	mu       sync.RWMutex
	items    map[string]*list.Element
	order    *list.List
	maxSize  int
	ttl      time.Duration
	onEvict  func(key string, value interface{})
}

// entry represents a cache entry
type entry struct {
	key       string
	value     interface{}
	expireAt  time.Time
	createdAt time.Time
}

// New creates a new cache
func New(maxSize int, ttl time.Duration) *Cache {
	return &Cache{
		items:   make(map[string]*list.Element),
		order:   list.New(),
		maxSize: maxSize,
		ttl:     ttl,
	}
}

// SetOnEvict sets the eviction callback
func (c *Cache) SetOnEvict(fn func(key string, value interface{})) {
	c.onEvict = fn
}

// Set adds an item to the cache
func (c *Cache) Set(key string, value interface{}) {
	c.SetWithTTL(key, value, c.ttl)
}

// SetWithTTL adds an item with custom TTL
func (c *Cache) SetWithTTL(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	expireAt := now.Add(ttl)

	// Check if key exists
	if elem, ok := c.items[key]; ok {
		// Update existing entry
		entry := elem.Value.(*entry)
		entry.value = value
		entry.expireAt = expireAt
		c.order.MoveToFront(elem)
		return
	}

	// Evict if at capacity
	if c.maxSize > 0 && c.order.Len() >= c.maxSize {
		c.evictOldest()
	}

	// Add new entry
	e := c.order.PushFront(&entry{
		key:       key,
		value:     value,
		expireAt:  expireAt,
		createdAt: now,
	})
	c.items[key] = e
}

// Get retrieves an item from the cache
func (c *Cache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	elem, ok := c.items[key]
	if !ok {
		return nil, false
	}

	entry := elem.Value.(*entry)

	// Check expiration
	if !entry.expireAt.IsZero() && time.Now().After(entry.expireAt) {
		return nil, false
	}

	// Move to front (LRU)
	c.order.MoveToFront(elem)

	return entry.value, true
}

// GetOrSet retrieves an item or sets it if not found
func (c *Cache) GetOrSet(key string, factory func() interface{}) interface{} {
	if value, ok := c.Get(key); ok {
		return value
	}

	value := factory()
	c.Set(key, value)
	return value
}

// Has checks if a key exists and is not expired
func (c *Cache) Has(key string) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()

	elem, ok := c.items[key]
	if !ok {
		return false
	}

	entry := elem.Value.(*entry)
	if !entry.expireAt.IsZero() && time.Now().After(entry.expireAt) {
		return false
	}

	return true
}

// Delete removes an item from the cache
func (c *Cache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	elem, ok := c.items[key]
	if !ok {
		return
	}

	c.order.Remove(elem)
	delete(c.items, key)
}

// Clear removes all items from the cache
func (c *Cache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.onEvict != nil {
		for _, elem := range c.items {
			entry := elem.Value.(*entry)
			c.onEvict(entry.key, entry.value)
		}
	}

	c.items = make(map[string]*list.Element)
	c.order = list.New()
}

// Len returns the number of items in the cache
func (c *Cache) Len() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.order.Len()
}

// Keys returns all keys in the cache
func (c *Cache) Keys() []string {
	c.mu.RLock()
	defer c.mu.RUnlock()

	keys := make([]string, 0, len(c.items))
	for k := range c.items {
		keys = append(keys, k)
	}
	return keys
}

// evictOldest removes the oldest item
func (c *Cache) evictOldest() {
	elem := c.order.Back()
	if elem == nil {
		return
	}

	entry := elem.Value.(*entry)
	c.order.Remove(elem)
	delete(c.items, entry.key)

	if c.onEvict != nil {
		c.onEvict(entry.key, entry.value)
	}
}

// Cleanup removes expired items
func (c *Cache) Cleanup() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	for elem := c.order.Back(); elem != nil; elem = elem.Prev() {
		entry := elem.Value.(*entry)
		if !entry.expireAt.IsZero() && now.After(entry.expireAt) {
			c.order.Remove(elem)
			delete(c.items, entry.key)
			if c.onEvict != nil {
				c.onEvict(entry.key, entry.value)
			}
		}
	}
}

// StartCleanup starts periodic cleanup
func (c *Cache) StartCleanup(ctx context.Context, interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				c.Cleanup()
			}
		}
	}()
}

// ============================================================================
// Specialized Caches
// ============================================================================

// MarketDataCache is a cache for market data
type MarketDataCache struct {
	*Cache
}

// NewMarketDataCache creates a market data cache
func NewMarketDataCache(maxSize int) *MarketDataCache {
	cache := New(maxSize, 5*time.Minute)
	return &MarketDataCache{Cache: cache}
}

// MarketDataEntry represents market data
type MarketDataEntry struct {
	Symbol    string
	Interval  string
	Open      float64
	High      float64
	Low       float64
	Close     float64
	Volume    float64
	Timestamp time.Time
}

// GetKey generates a cache key for market data
func GetMarketDataKey(symbol, interval string, limit int) string {
	return "market:" + symbol + ":" + interval + ":" + string(rune(limit))
}

// StrategyCache is a cache for strategies
type StrategyCache struct {
	*Cache
}

// NewStrategyCache creates a strategy cache
func NewStrategyCache(maxSize int) *StrategyCache {
	cache := New(maxSize, 10*time.Minute)
	return &StrategyCache{Cache: cache}
}

// GetKey generates a cache key for a strategy
func GetStrategyKey(id string) string {
	return "strategy:" + id
}

// CapsuleCache is a cache for capsules
type CapsuleCache struct {
	*Cache
}

// NewCapsuleCache creates a capsule cache
func NewCapsuleCache(maxSize int) *CapsuleCache {
	cache := New(maxSize, 15*time.Minute)
	return &CapsuleCache{Cache: cache}
}

// GetKey generates a cache key for a capsule
func GetCapsuleKey(name, version string) string {
	return "capsule:" + name + ":" + version
}
