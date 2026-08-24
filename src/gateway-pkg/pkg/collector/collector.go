// Package collector provides market data collection for NEMT Gateway
package collector

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/nemt-lab/nemt-go/pkg/cache"
	"github.com/nemt-lab/nemt-go/pkg/logger"
)

// Binance WebSocket message structures
type BinanceTicker struct {
	Symbol    string  `json:"s"`
	Price    string  `json:"p"`
	Percent  string  `json:"P"`
	Volume   string  `json:"v"`
	High     string  `json:"h"`
	Low      string  `json:"l"`
	Open     string  `json:"o"`
	EventTime int64  `json:"E"`
}

type BinanceKline struct {
	Symbol    string  `json:"s"`
	Interval  string  `json:"i"`
	OpenTime  int64   `json:"t"`
	Open      float64 `json:"o"`
	High      float64 `json:"h"`
	Low       float64 `json:"l"`
	Close     float64 `json:"c"`
	Volume    float64 `json:"v"`
	CloseTime int64   `json:"T"`
	EventTime int64   `json:"E"`
}

// KlineData represents parsed kline data
type KlineData struct {
	Symbol    string    `json:"symbol"`
	Interval  string    `json:"interval"`
	OpenTime  time.Time `json:"open_time"`
	Open      float64   `json:"open"`
	High      float64   `json:"high"`
	Low       float64   `json:"low"`
	Close     float64   `json:"close"`
	Volume    float64   `json:"volume"`
	CloseTime time.Time `json:"close_time"`
	Timestamp time.Time `json:"timestamp"`
}

// TickerData represents parsed ticker data
type TickerData struct {
	Symbol    string    `json:"symbol"`
	Price     float64   `json:"price"`
	Percent   float64   `json:"percent"`
	Volume    float64   `json:"volume"`
	High      float64   `json:"high"`
	Low       float64   `json:"low"`
	Open      float64   `json:"open"`
	Timestamp time.Time `json:"timestamp"`
}

// Collector manages market data collection
type Collector struct {
	log       *logger.Logger
	cache     *cache.MarketDataCache
	subs      map[string]map[*Subscriber]bool
	mu        sync.RWMutex
	ctx       context.Context
	cancel    context.CancelFunc
}

// Subscriber represents a WebSocket subscriber
type Subscriber struct {
	ID      string
	Symbols []string
	Conn    *websocket.Conn
	Send    chan []byte
}

// NewCollector creates a new market data collector
func NewCollector(log *logger.Logger) *Collector {
	ctx, cancel := context.WithCancel(context.Background())
	return &Collector{
		log:   log,
		cache: cache.NewMarketDataCache(10000),
		subs:  make(map[string]map[*Subscriber]bool),
		ctx:   ctx,
		cancel: cancel,
	}
}

// Start starts the collector
func (c *Collector) Start() error {
	c.log.Info("Starting market data collector", nil)

	// Start WebSocket client to Binance (placeholder)
	// In production, this would connect to exchange WebSocket APIs
	go c.simulateMarketData()

	return nil
}

// Stop stops the collector
func (c *Collector) Stop() {
	c.cancel()
	c.log.Info("Market data collector stopped", nil)
}

// Subscribe subscribes to market data updates
func (c *Collector) Subscribe(sub *Subscriber) {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, symbol := range sub.Symbols {
		c.subs[symbol][sub] = true
	}

	c.log.Info("Subscriber added", map[string]interface{}{
		"id":      sub.ID,
		"symbols": sub.Symbols,
	})
}

// Unsubscribe unsubscribes from market data
func (c *Collector) Unsubscribe(sub *Subscriber) {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, symbol := range sub.Symbols {
		delete(c.subs[symbol], sub)
	}

	c.log.Info("Subscriber removed", map[string]interface{}{
		"id": sub.ID,
	})
}

// Broadcast sends data to all subscribers of a symbol
func (c *Collector) Broadcast(symbol string, data []byte) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if subs, ok := c.subs[symbol]; ok {
		for sub := range subs {
			select {
			case sub.Send <- data:
			default:
				// Subscriber buffer full, skip
			}
		}
	}
}

// GetLatestTicker returns the latest ticker for a symbol
func (c *Collector) GetLatestTicker(symbol string) (*TickerData, bool) {
	data, ok := c.cache.Get(cache.GetMarketDataKey(symbol, "ticker", 1))
	if !ok {
		return nil, false
	}
	ticker, ok := data.(*TickerData)
	return ticker, ok
}

// GetLatestKline returns the latest kline for a symbol and interval
func (c *Collector) GetLatestKline(symbol, interval string) (*KlineData, bool) {
	data, ok := c.cache.Get(cache.GetMarketDataKey(symbol, interval, 1))
	if !ok {
		return nil, false
	}
	kline, ok := data.(*KlineData)
	return kline, ok
}

// simulateMarketData simulates market data for testing
func (c *Collector) simulateMarketData() {
	ticker := &TickerData{
		Symbol:    "BTCUSDT",
		Price:    67432.50,
		Percent:  2.35,
		Volume:   12543.21,
		High:     68000.00,
		Low:      66000.00,
		Open:     65800.00,
		Timestamp: time.Now(),
	}

	tickerChan := make(chan *TickerData)
	klineChan := make(chan *KlineData)

	// Start ticker simulation
	go func() {
		basePrice := 67432.50
		for {
			select {
			case <-c.ctx.Done():
				return
			case <-time.After(1 * time.Second):
				// Simulate price movement
				change := (float64(time.Now().UnixNano()%1000) - 500) / 100
				ticker.Price = basePrice + change
				ticker.Percent = (ticker.Price - ticker.Open) / ticker.Open * 100
				ticker.Timestamp = time.Now()

				// Cache it
				c.cache.Set(cache.GetMarketDataKey(ticker.Symbol, "ticker", 1), ticker)

				// Broadcast
				data, _ := json.Marshal(ticker)
				c.Broadcast(ticker.Symbol, data)

				select {
				case tickerChan <- ticker:
				default:
				}
			}
		}
	}()

	// Start kline simulation (1 minute intervals)
	go func() {
		basePrice := 67432.50
		kline := &KlineData{
			Symbol:    "BTCUSDT",
			Interval:  "1m",
			OpenTime:  time.Now().Truncate(time.Minute),
			Open:      basePrice,
			High:      basePrice,
			Low:       basePrice,
			Close:     basePrice,
			Volume:    100.0,
			CloseTime: time.Now().Truncate(time.Minute).Add(time.Minute),
			Timestamp: time.Now(),
		}

		for {
			select {
			case <-c.ctx.Done():
				return
			case <-time.After(5 * time.Second):
				// Update kline
				change := (float64(time.Now().UnixNano()%1000) - 500) / 100
				kline.Close = kline.Open + change
				if kline.Close > kline.High {
					kline.High = kline.Close
				}
				if kline.Close < kline.Low {
					kline.Low = kline.Close
				}
				kline.Volume += 10.0
				kline.Timestamp = time.Now()

				// Cache it
				c.cache.Set(cache.GetMarketDataKey(kline.Symbol, kline.Interval, 1), kline)

				// Broadcast
				data, _ := json.Marshal(kline)
				c.Broadcast(kline.Symbol, data)

				select {
				case klineChan <- kline:
				default:
				}
			}
		}
	}()

	// Log ticker updates
	go func() {
		for {
			select {
			case <-c.ctx.Done():
				return
			case t := <-tickerChan:
				c.log.Debug(fmt.Sprintf("Ticker: %s $%.2f (%.2f%%)", t.Symbol, t.Price, t.Percent), nil)
			}
		}
	}()
}

// GetSubscribers returns the number of subscribers for a symbol
func (c *Collector) GetSubscribers(symbol string) int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.subs[symbol])
}

// GetTotalSubscribers returns total number of subscribers
func (c *Collector) GetTotalSubscribers() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	total := 0
	for _, subs := range c.subs {
		total += len(subs)
	}
	return total
}
