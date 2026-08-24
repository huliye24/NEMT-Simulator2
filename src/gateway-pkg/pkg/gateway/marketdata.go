// Package gateway provides HTTP handlers for Market Data API
package gateway

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/collector"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
	"github.com/nemt-lab/nemt-go/pkg/models"
)

// MarketDataHandler handles Market Data API requests
type MarketDataHandler struct {
	log       *logger.Logger
	collector *collector.Collector
}

// NewMarketDataHandler creates a new MarketDataHandler
func NewMarketDataHandler(log *logger.Logger, col *collector.Collector) *MarketDataHandler {
	return &MarketDataHandler{
		log:       log,
		collector: col,
	}
}

// Get returns market data for a symbol
func (h *MarketDataHandler) Get(c *gin.Context) {
	symbol := c.Param("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_SYMBOL", "Symbol is required"))
		return
	}

	interval := c.DefaultQuery("interval", "1h")
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	h.log.Info("Getting market data", map[string]interface{}{
		"symbol":   symbol,
		"interval": interval,
		"limit":    limit,
	})

	// Validate interval
	validIntervals := map[string]bool{
		"1m": true, "5m": true, "15m": true, "30m": true,
		"1h": true, "4h": true, "1d": true, "1w": true,
	}
	if !validIntervals[interval] {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_INTERVAL", "Invalid interval"))
		return
	}

	// Try to get from collector cache
	if h.collector != nil {
		if kline, ok := h.collector.GetLatestKline(symbol, interval); ok {
			c.JSON(http.StatusOK, common.NewSuccessResponse(kline))
			return
		}
	}

	c.JSON(http.StatusOK, common.NewSuccessResponse(map[string]interface{}{
		"symbol":   symbol,
		"interval": interval,
		"data":     []models.MarketData{},
	}))
}

// Subscribe subscribes to real-time market data (SSE)
func (h *MarketDataHandler) Subscribe(c *gin.Context) {
	symbol := c.Param("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_SYMBOL", "Symbol is required"))
		return
	}

	interval := c.DefaultQuery("interval", "1h")

	h.log.Info("Subscribing to market data", map[string]interface{}{
		"symbol":   symbol,
		"interval": interval,
	})

	// Set SSE headers
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("Access-Control-Allow-Origin", "*")

	c.SSEvent("connected", gin.H{
		"symbol":   symbol,
		"interval": interval,
		"status":   "subscribed",
	})

	c.SSEvent("ping", gin.H{"timestamp": common.TimestampNow()})
}

// GetLatest returns the latest price for a symbol
func (h *MarketDataHandler) GetLatest(c *gin.Context) {
	symbol := c.Param("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_SYMBOL", "Symbol is required"))
		return
	}

	h.log.Info("Getting latest price", map[string]interface{}{"symbol": symbol})

	if h.collector != nil {
		if ticker, ok := h.collector.GetLatestTicker(symbol); ok {
			c.JSON(http.StatusOK, common.NewSuccessResponse(ticker))
			return
		}
	}

	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Symbol not found"))
}

// GetOHLCV returns OHLCV data
func (h *MarketDataHandler) GetOHLCV(c *gin.Context) {
	symbol := c.Param("symbol")
	interval := c.DefaultQuery("interval", "1h")

	h.log.Info("Getting OHLCV data", map[string]interface{}{
		"symbol":   symbol,
		"interval": interval,
	})

	c.JSON(http.StatusOK, common.NewSuccessResponse(map[string]interface{}{
		"symbol":   symbol,
		"interval": interval,
		"data":     []interface{}{},
	}))
}

// GetSupportedSymbols returns list of supported symbols
func (h *MarketDataHandler) GetSupportedSymbols(c *gin.Context) {
	h.log.Info("Getting supported symbols", nil)

	c.JSON(http.StatusOK, common.NewSuccessResponse([]string{
		"BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT",
	}))
}

// GetSupportedIntervals returns list of supported intervals
func (h *MarketDataHandler) GetSupportedIntervals(c *gin.Context) {
	h.log.Info("Getting supported intervals", nil)

	c.JSON(http.StatusOK, common.NewSuccessResponse([]map[string]string{
		{"interval": "1m", "description": "1 minute"},
		{"interval": "5m", "description": "5 minutes"},
		{"interval": "15m", "description": "15 minutes"},
		{"interval": "30m", "description": "30 minutes"},
		{"interval": "1h", "description": "1 hour"},
		{"interval": "4h", "description": "4 hours"},
		{"interval": "1d", "description": "1 day"},
		{"interval": "1w", "description": "1 week"},
	}))
}
