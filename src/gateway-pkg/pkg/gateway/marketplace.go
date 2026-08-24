// Package gateway provides HTTP handlers for Marketplace API
package gateway

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
	"github.com/nemt-lab/nemt-go/pkg/market"
)

// MarketplaceHandler handles marketplace API requests
type MarketplaceHandler struct {
	log      *logger.Logger
	market   *market.MarketplaceService
	capsules *market.CapsuleMarketplaceService
}

// NewMarketplaceHandler creates a new MarketplaceHandler
func NewMarketplaceHandler(log *logger.Logger) *MarketplaceHandler {
	return &MarketplaceHandler{
		log:      log,
		market:   market.NewMarketplaceService(),
		capsules: market.NewCapsuleMarketplaceService(),
	}
}

// ============================================================================
// Strategy Marketplace
// ============================================================================

// ListStrategyListings returns all strategy listings
func (h *MarketplaceHandler) ListStrategyListings(c *gin.Context) {
	filter := market.MarketplaceFilter{
		Type:    c.Query("type"),
		Status:  c.Query("status"),
		Author:  c.Query("author"),
		SortBy:  c.DefaultQuery("sort_by", "recent"),
		Page:    1,
		PageSize: 20,
	}

	listings, total, err := h.market.ListStrategies(filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("INTERNAL_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusOK, common.NewPaginatedResponse(listings, filter.Page, filter.PageSize, total))
}

// GetStrategyListing returns a single strategy listing
func (h *MarketplaceHandler) GetStrategyListing(c *gin.Context) {
	id := c.Param("id")

	listing, found := h.market.GetStrategy(id)
	if !found {
		c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Strategy listing not found"))
		return
	}

	c.JSON(http.StatusOK, common.NewSuccessResponse(listing))
}

// CreateStrategyListing creates a new strategy listing
func (h *MarketplaceHandler) CreateStrategyListing(c *gin.Context) {
	var req market.StrategyListing
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	if err := h.market.CreateListing(&req); err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("CREATE_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusCreated, common.NewSuccessResponse(req))
}

// UpdateStrategyListing updates a strategy listing
func (h *MarketplaceHandler) UpdateStrategyListing(c *gin.Context) {
	id := c.Param("id")

	var req market.StrategyListing
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	if err := h.market.UpdateListing(id, &req); err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("UPDATE_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusOK, common.NewSuccessResponse(nil))
}

// DeleteStrategyListing deletes a strategy listing
func (h *MarketplaceHandler) DeleteStrategyListing(c *gin.Context) {
	id := c.Param("id")

	if err := h.market.DeleteListing(id); err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("DELETE_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusOK, common.NewSuccessResponse(nil))
}

// ============================================================================
// Capsule Marketplace
// ============================================================================

// ListCapsuleListings returns all capsule listings
func (h *MarketplaceHandler) ListCapsuleListings(c *gin.Context) {
	filter := market.CapsuleFilter{
		Type:    c.Query("type"),
		Status:  c.Query("status"),
		Author:  c.Query("author"),
		SortBy:  c.DefaultQuery("sort_by", "recent"),
		Page:    1,
		PageSize: 20,
	}

	listings, total, err := h.capsules.ListCapsules(filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("INTERNAL_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusOK, common.NewPaginatedResponse(listings, filter.Page, filter.PageSize, total))
}

// GetCapsuleListing returns a single capsule listing
func (h *MarketplaceHandler) GetCapsuleListing(c *gin.Context) {
	id := c.Param("id")

	listing, found := h.capsules.GetCapsule(id)
	if !found {
		c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Capsule listing not found"))
		return
	}

	c.JSON(http.StatusOK, common.NewSuccessResponse(listing))
}

// CreateCapsuleListing creates a new capsule listing
func (h *MarketplaceHandler) CreateCapsuleListing(c *gin.Context) {
	var req market.CapsuleListing
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	if err := h.capsules.CreateListing(&req); err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("CREATE_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusCreated, common.NewSuccessResponse(req))
}

// UpdateCapsuleListing updates a capsule listing
func (h *MarketplaceHandler) UpdateCapsuleListing(c *gin.Context) {
	id := c.Param("id")

	var req market.CapsuleListing
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	if err := h.capsules.UpdateListing(id, &req); err != nil {
		c.JSON(http.StatusInternalServerError, common.NewErrorResponse("UPDATE_ERROR", err.Error()))
		return
	}

	c.JSON(http.StatusOK, common.NewSuccessResponse(nil))
}
