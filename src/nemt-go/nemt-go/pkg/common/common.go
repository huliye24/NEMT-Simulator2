// Package common provides common utilities for NEMT Gateway
package common

import (
	"crypto/rand"
	"encoding/hex"
	"time"

	"github.com/google/uuid"
)

// GenerateUUID generates a new UUID v4
func GenerateUUID() string {
	return uuid.New().String()
}

// GenerateRequestID generates a request ID
func GenerateRequestID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

// TimestampNow returns current Unix timestamp in milliseconds
func TimestampNow() int64 {
	return time.Now().UnixMilli()
}

// TimestampSeconds returns current Unix timestamp in seconds
func TimestampSeconds() int64 {
	return time.Now().Unix()
}

// FormatTimestamp formats a timestamp to RFC3339
func FormatTimestamp(ts int64) string {
	return time.UnixMilli(ts).Format(time.RFC3339)
}

// Response represents a standard API response
type Response struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   *ErrorInfo  `json:"error,omitempty"`
	Meta    *MetaInfo   `json:"meta,omitempty"`
}

// ErrorInfo represents error details
type ErrorInfo struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Details string `json:"details,omitempty"`
}

// MetaInfo represents response metadata
type MetaInfo struct {
	RequestID  string `json:"request_id,omitempty"`
	Timestamp  int64  `json:"timestamp"`
	Page       int    `json:"page,omitempty"`
	PageSize   int    `json:"page_size,omitempty"`
	TotalCount int    `json:"total_count,omitempty"`
}

// NewSuccessResponse creates a success response
func NewSuccessResponse(data interface{}) Response {
	return Response{
		Success: true,
		Data:    data,
		Meta: &MetaInfo{
			Timestamp: TimestampNow(),
		},
	}
}

// NewErrorResponse creates an error response
func NewErrorResponse(code, message string) Response {
	return Response{
		Success: false,
		Error: &ErrorInfo{
			Code:    code,
			Message: message,
		},
		Meta: &MetaInfo{
			Timestamp: TimestampNow(),
		},
	}
}

// NewPaginatedResponse creates a paginated response
func NewPaginatedResponse(data interface{}, page, pageSize, totalCount int) Response {
	return Response{
		Success: true,
		Data:    data,
		Meta: &MetaInfo{
			Timestamp:  TimestampNow(),
			Page:       page,
			PageSize:   pageSize,
			TotalCount: totalCount,
		},
	}
}

// PageRequest represents pagination parameters
type PageRequest struct {
	Page     int `form:"page" binding:"min=1"`
	PageSize int `form:"page_size" binding:"min=1,max=100"`
}

// NormalizePage normalizes pagination parameters
func (p *PageRequest) Normalize() {
	if p.Page <= 0 {
		p.Page = 1
	}
	if p.PageSize <= 0 {
		p.PageSize = 20
	}
	if p.PageSize > 100 {
		p.PageSize = 100
	}
}

// Offset calculates the offset for database queries
func (p *PageRequest) Offset() int {
	return (p.Page - 1) * p.PageSize
}
