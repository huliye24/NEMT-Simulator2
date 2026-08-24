// Package gateway provides HTTP handlers for Strategy API
package gateway

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
	"github.com/nemt-lab/nemt-go/pkg/models"
)

// StrategyHandler handles Strategy API requests
type StrategyHandler struct {
	log *logger.Logger
}

// NewStrategyHandler creates a new StrategyHandler
func NewStrategyHandler(log *logger.Logger) *StrategyHandler {
	return &StrategyHandler{log: log}
}

// List returns all strategies
func (h *StrategyHandler) List(c *gin.Context) {
	// Parse query parameters
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	strategyType := c.Query("type")
	status := c.Query("status")

	h.log.Info("Listing strategies", map[string]interface{}{
		"page":   page,
		"filter": map[string]string{"type": strategyType, "status": status},
	})

	// TODO: Query database with filters
	// For now, return empty list with pagination metadata
	c.JSON(http.StatusOK, common.NewPaginatedResponse([]models.Strategy{}, page, pageSize, 0))
}

// Get returns a single strategy by ID
func (h *StrategyHandler) Get(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Strategy ID is required"))
		return
	}

	h.log.Info("Getting strategy", map[string]interface{}{"id": id})

	// TODO: Query database
	// For now, return 404
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Strategy not found"))
}

// Create creates a new strategy
func (h *StrategyHandler) Create(c *gin.Context) {
	var req models.CreateStrategyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	h.log.Info("Creating strategy", map[string]interface{}{
		"name": req.Name,
		"type": req.Type,
	})

	// Validate request
	if req.Name == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("VALIDATION_ERROR", "Strategy name is required"))
		return
	}

	// Create strategy model
	strategy := models.Strategy{
		ID:          common.GenerateUUID(),
		Name:        req.Name,
		Author:      req.Author,
		Type:        models.StrategyType(req.Type),
		Code:        req.Code,
		Status:      models.StrategyDraft,
		SharpeRatio: 0,
		MaxDrawdown: 0,
		TotalTrades: 0,
		WinRate:     0,
	}

	// TODO: Save to database

	h.log.Info("Strategy created", map[string]interface{}{"id": strategy.ID})

	c.JSON(http.StatusCreated, common.NewSuccessResponse(strategy))
}

// Update updates an existing strategy
func (h *StrategyHandler) Update(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Strategy ID is required"))
		return
	}

	var req models.UpdateStrategyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	h.log.Info("Updating strategy", map[string]interface{}{"id": id, "name": req.Name})

	// TODO: Update in database
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Strategy not found"))
}

// Delete deletes a strategy
func (h *StrategyHandler) Delete(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Strategy ID is required"))
		return
	}

	h.log.Info("Deleting strategy", map[string]interface{}{"id": id})

	// TODO: Delete from database
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Strategy not found"))
}

// Clone clones an existing strategy
func (h *StrategyHandler) Clone(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Strategy ID is required"))
		return
	}

	h.log.Info("Cloning strategy", map[string]interface{}{"source_id": id})

	// TODO: Clone strategy in database
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Strategy not found"))
}
