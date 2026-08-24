// Package gateway provides HTTP handlers for NEMT Gateway
package gateway

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
)

// Handler holds HTTP handlers
type Handler struct {
	log *logger.Logger
}

// NewHandler creates a new Handler
func NewHandler(log *logger.Logger) *Handler {
	return &Handler{log: log}
}

// Health handles health check requests
func (h *Handler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "nemt-gateway",
		"version": "1.0.0",
	})
}

// Ready handles readiness check requests
func (h *Handler) Ready(c *gin.Context) {
	// TODO: Check database and Redis connections
	c.JSON(http.StatusOK, gin.H{
		"status": "ready",
	})
}

// Error handles error responses
func (h *Handler) Error(c *gin.Context, status int, code, message string) {
	c.JSON(status, common.NewErrorResponse(code, message))
}

// NotFound handles 404 errors
func (h *Handler) NotFound(c *gin.Context) {
	h.Error(c, http.StatusNotFound, "NOT_FOUND", "Resource not found")
}

// MethodNotAllowed handles 405 errors
func (h *Handler) MethodNotAllowed(c *gin.Context) {
	h.Error(c, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "Method not allowed")
}

// InternalError handles 500 errors
func (h *Handler) InternalError(c *gin.Context, err error) {
	h.log.Error("Internal server error", err, nil)
	h.Error(c, http.StatusInternalServerError, "INTERNAL_ERROR", "Internal server error")
}
