// Package gateway provides HTTP handlers for Backtest API
package gateway

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
	"github.com/nemt-lab/nemt-go/pkg/models"
)

// BacktestHandler handles Backtest API requests
type BacktestHandler struct {
	log *logger.Logger
}

// NewBacktestHandler creates a new BacktestHandler
func NewBacktestHandler(log *logger.Logger) *BacktestHandler {
	return &BacktestHandler{log: log}
}

// Start starts a new backtest
func (h *BacktestHandler) Start(c *gin.Context) {
	var req models.BacktestRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	h.log.Info("Starting backtest", map[string]interface{}{
		"strategy_id": req.StrategyID,
		"symbol":      req.Symbol,
		"interval":    req.Interval,
	})

	// Validate request
	if req.StrategyID == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("VALIDATION_ERROR", "Strategy ID is required"))
		return
	}
	if req.Symbol == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("VALIDATION_ERROR", "Symbol is required"))
		return
	}

	// Generate backtest ID
	backtestID := common.GenerateUUID()

	// TODO: Start backtest job
	// - Load strategy from database
	// - Initialize Python engine via gRPC
	// - Stream results via Server-Sent Events or WebSocket

	// Return backtest ID for polling
	c.JSON(http.StatusAccepted, common.NewSuccessResponse(map[string]interface{}{
		"backtest_id": backtestID,
		"status":      "pending",
		"message":     "Backtest started. Poll /api/v1/backtest/" + backtestID + " for status",
	}))
}

// Get returns a backtest result
func (h *BacktestHandler) Get(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Backtest ID is required"))
		return
	}

	h.log.Info("Getting backtest result", map[string]interface{}{"id": id})

	// TODO: Query database for backtest result
	// For now, return not found
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Backtest not found"))
}

// GetProgress returns backtest progress
func (h *BacktestHandler) GetProgress(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Backtest ID is required"))
		return
	}

	h.log.Info("Getting backtest progress", map[string]interface{}{"id": id})

	// TODO: Return current progress from job queue
	c.JSON(http.StatusOK, common.NewSuccessResponse(map[string]interface{}{
		"backtest_id": id,
		"status":      "pending",
		"progress":    0,
		"current_bar": 0,
		"total_bars":  0,
	}))
}

// Cancel cancels a running backtest
func (h *BacktestHandler) Cancel(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Backtest ID is required"))
		return
	}

	h.log.Info("Cancelling backtest", map[string]interface{}{"id": id})

	// TODO: Cancel backtest job
	c.JSON(http.StatusOK, common.NewSuccessResponse(map[string]interface{}{
		"backtest_id": id,
		"status":      "cancelled",
	}))
}

// List returns all backtests
func (h *BacktestHandler) List(c *gin.Context) {
	page := c.DefaultQuery("page", "1")
	strategyID := c.Query("strategy_id")

	h.log.Info("Listing backtests", map[string]interface{}{
		"page":        page,
		"strategy_id": strategyID,
	})

	// TODO: Query database for backtests
	c.JSON(http.StatusOK, common.NewPaginatedResponse([]models.BacktestReport{}, 1, 20, 0))
}

// GetEquityCurve returns the equity curve for a backtest
func (h *BacktestHandler) GetEquityCurve(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Backtest ID is required"))
		return
	}

	h.log.Info("Getting equity curve", map[string]interface{}{"id": id})

	// TODO: Return equity curve data
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Backtest not found"))
}

// GetTrades returns the trades for a backtest
func (h *BacktestHandler) GetTrades(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Backtest ID is required"))
		return
	}

	h.log.Info("Getting trades", map[string]interface{}{"id": id})

	// TODO: Return trades data
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Backtest not found"))
}
