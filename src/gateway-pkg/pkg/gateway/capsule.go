// Package gateway provides HTTP handlers for Capsule API
package gateway

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
	"github.com/nemt-lab/nemt-go/pkg/models"
)

// CapsuleHandler handles Capsule API requests
type CapsuleHandler struct {
	log *logger.Logger
}

// NewCapsuleHandler creates a new CapsuleHandler
func NewCapsuleHandler(log *logger.Logger) *CapsuleHandler {
	return &CapsuleHandler{log: log}
}

// List returns all capsules
func (h *CapsuleHandler) List(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	capsuleType := c.Query("type")
	version := c.Query("version")

	h.log.Info("Listing capsules", map[string]interface{}{
		"page":   page,
		"filter": map[string]string{"type": capsuleType, "version": version},
	})

	// TODO: Query database with filters
	c.JSON(http.StatusOK, common.NewPaginatedResponse([]models.Capsule{}, page, pageSize, 0))
}

// Get returns a single capsule by ID
func (h *CapsuleHandler) Get(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Capsule ID is required"))
		return
	}

	h.log.Info("Getting capsule", map[string]interface{}{"id": id})

	// TODO: Query database
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Capsule not found"))
}

// Register registers a new capsule
func (h *CapsuleHandler) Register(c *gin.Context) {
	var req models.RegisterCapsuleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	h.log.Info("Registering capsule", map[string]interface{}{
		"name":    req.Name,
		"version": req.Version,
		"type":    req.Type,
	})

	// Validate request
	if req.Name == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("VALIDATION_ERROR", "Capsule name is required"))
		return
	}
	if req.Version == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("VALIDATION_ERROR", "Capsule version is required"))
		return
	}

	// Create capsule model
	capsule := models.Capsule{
		ID:           common.GenerateUUID(),
		Name:         req.Name,
		Version:      req.Version,
		Author:       req.Author,
		Type:         models.CapsuleType(req.Type),
		Code:         req.Code,
		Dependencies: "", // JSON array
	}

	// TODO: Save to database

	h.log.Info("Capsule registered", map[string]interface{}{"id": capsule.ID})

	c.JSON(http.StatusCreated, common.NewSuccessResponse(capsule))
}

// Update updates an existing capsule
func (h *CapsuleHandler) Update(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Capsule ID is required"))
		return
	}

	var req models.UpdateCapsuleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_REQUEST", err.Error()))
		return
	}

	h.log.Info("Updating capsule", map[string]interface{}{"id": id})

	// TODO: Update in database
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Capsule not found"))
}

// Delete deletes a capsule
func (h *CapsuleHandler) Delete(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_ID", "Capsule ID is required"))
		return
	}

	h.log.Info("Deleting capsule", map[string]interface{}{"id": id})

	// TODO: Delete from database
	c.JSON(http.StatusNotFound, common.NewErrorResponse("NOT_FOUND", "Capsule not found"))
}

// GetVersions returns all versions of a capsule
func (h *CapsuleHandler) GetVersions(c *gin.Context) {
	name := c.Param("name")
	if name == "" {
		c.JSON(http.StatusBadRequest, common.NewErrorResponse("INVALID_NAME", "Capsule name is required"))
		return
	}

	h.log.Info("Getting capsule versions", map[string]interface{}{"name": name})

	// TODO: Query database for all versions
	c.JSON(http.StatusOK, common.NewSuccessResponse([]models.Capsule{}))
}
