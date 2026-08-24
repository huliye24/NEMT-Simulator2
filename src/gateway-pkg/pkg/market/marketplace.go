// Package market provides strategy and capsule marketplace functionality
package market

import (
	"time"

	"github.com/google/uuid"
)

func generateUUID() string {
	return uuid.New().String()
}

// ============================================================================
// Strategy Marketplace
// ============================================================================

// StrategyListing represents a strategy in the marketplace
type StrategyListing struct {
	ID          string          `json:"id"`
	Name        string          `json:"name"`
	Author      string          `json:"author"`
	Type        string          `json:"type"`
	Description string          `json:"description"`
	Tags        []string        `json:"tags"`
	Metrics     StrategyMetrics `json:"metrics"`
	Pricing     PricingInfo     `json:"pricing"`
	Status      string          `json:"status"`
	Downloads   int             `json:"downloads"`
	Rating      float64         `json:"rating"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

// StrategyMetrics represents strategy performance metrics
type StrategyMetrics struct {
	SharpeRatio  float64 `json:"sharpe_ratio"`
	MaxDrawdown  float64 `json:"max_drawdown"`
	TotalTrades  int     `json:"total_trades"`
	WinRate      float64 `json:"win_rate"`
	ProfitFactor float64 `json:"profit_factor"`
	AnnualReturn float64 `json:"annual_return"`
}

// PricingInfo represents pricing model
type PricingInfo struct {
	Type      string  `json:"type"` // free, subscription, onetime
	Price     float64 `json:"price"`
	Currency  string  `json:"currency"`
	Period    string  `json:"period,omitempty"` // monthly, yearly
	TrialDays int     `json:"trial_days,omitempty"`
}

// MarketplaceService provides marketplace operations
type MarketplaceService struct {
	// In production, this would connect to a database
	listings map[string]*StrategyListing
}

// NewMarketplaceService creates a new marketplace service
func NewMarketplaceService() *MarketplaceService {
	return &MarketplaceService{
		listings: make(map[string]*StrategyListing),
	}
}

// ListStrategies returns all marketplace strategies
func (s *MarketplaceService) ListStrategies(filter MarketplaceFilter) ([]*StrategyListing, int, error) {
	var results []*StrategyListing

	for _, listing := range s.listings {
		if s.matchesFilter(listing, filter) {
			results = append(results, listing)
		}
	}

	return results, len(results), nil
}

// GetStrategy returns a single strategy listing
func (s *MarketplaceService) GetStrategy(id string) (*StrategyListing, bool) {
	listing, ok := s.listings[id]
	return listing, ok
}

// CreateListing creates a new marketplace listing
func (s *MarketplaceService) CreateListing(listing *StrategyListing) error {
	listing.ID = generateUUID()
	listing.CreatedAt = time.Now()
	listing.UpdatedAt = time.Now()
	listing.Downloads = 0
	listing.Rating = 0

	s.listings[listing.ID] = listing
	return nil
}

// UpdateListing updates an existing listing
func (s *MarketplaceService) UpdateListing(id string, update *StrategyListing) error {
	if _, ok := s.listings[id]; !ok {
		return ErrNotFound
	}

	listing := s.listings[id]
	listing.Name = update.Name
	listing.Description = update.Description
	listing.Tags = update.Tags
	listing.Pricing = update.Pricing
	listing.Status = update.Status
	listing.UpdatedAt = time.Now()

	return nil
}

// DeleteListing removes a listing
func (s *MarketplaceService) DeleteListing(id string) error {
	if _, ok := s.listings[id]; !ok {
		return ErrNotFound
	}

	delete(s.listings, id)
	return nil
}

// IncrementDownloads increments download count
func (s *MarketplaceService) IncrementDownloads(id string) error {
	if listing, ok := s.listings[id]; ok {
		listing.Downloads++
		return nil
	}
	return ErrNotFound
}

// matchesFilter checks if a listing matches the filter
func (s *MarketplaceService) matchesFilter(listing *StrategyListing, filter MarketplaceFilter) bool {
	if filter.Type != "" && listing.Type != filter.Type {
		return false
	}
	if filter.Status != "" && listing.Status != filter.Status {
		return false
	}
	if filter.MinRating > 0 && listing.Rating < filter.MinRating {
		return false
	}
	if filter.Author != "" && listing.Author != filter.Author {
		return false
	}
	return true
}

// MarketplaceFilter represents search/filter criteria
type MarketplaceFilter struct {
	Type       string
	Status     string
	Author     string
	Tags       []string
	MinRating  float64
	SortBy     string // rating, downloads, recent, price
	SortOrder  string // asc, desc
	Page       int
	PageSize   int
}

// Errors
var (
	ErrNotFound = &MarketplaceError{Code: "NOT_FOUND", Message: "Resource not found"}
	ErrConflict = &MarketplaceError{Code: "CONFLICT", Message: "Resource already exists"}
)

// MarketplaceError represents marketplace errors
type MarketplaceError struct {
	Code    string
	Message string
}

func (e *MarketplaceError) Error() string {
	return e.Message
}

// ============================================================================
// Capsule Marketplace
// ============================================================================

// CapsuleListing represents a capsule in the marketplace
type CapsuleListing struct {
	ID           string             `json:"id"`
	Name         string             `json:"name"`
	Version      string             `json:"version"`
	Author       string             `json:"author"`
	Type         string             `json:"type"`
	Description  string             `json:"description"`
	Tags         []string           `json:"tags"`
	Capabilities CapsuleCapabilities `json:"capabilities"`
	Dependencies []string           `json:"dependencies"`
	Pricing      PricingInfo        `json:"pricing"`
	Status       string             `json:"status"`
	Downloads    int                `json:"downloads"`
	Rating       float64            `json:"rating"`
	Verified     bool               `json:"verified"`
	CreatedAt    time.Time          `json:"created_at"`
	UpdatedAt    time.Time          `json:"updated_at"`
}

// CapsuleCapabilities represents capsule features
type CapsuleCapabilities struct {
	MarketData     bool     `json:"market_data"`
	SignalGen      bool     `json:"signal_gen"`
	RiskManagement bool     `json:"risk_management"`
	Execution      bool     `json:"execution"`
	MLModels       []string `json:"ml_models,omitempty"`
	APIs           []string `json:"apis,omitempty"`
}

// CapsuleMarketplaceService provides capsule marketplace operations
type CapsuleMarketplaceService struct {
	listings map[string]*CapsuleListing
}

// NewCapsuleMarketplaceService creates a new capsule marketplace service
func NewCapsuleMarketplaceService() *CapsuleMarketplaceService {
	return &CapsuleMarketplaceService{
		listings: make(map[string]*CapsuleListing),
	}
}

// ListCapsules returns all marketplace capsules
func (s *CapsuleMarketplaceService) ListCapsules(filter CapsuleFilter) ([]*CapsuleListing, int, error) {
	var results []*CapsuleListing

	for _, listing := range s.listings {
		if s.matchesFilter(listing, filter) {
			results = append(results, listing)
		}
	}

	return results, len(results), nil
}

// GetCapsule returns a single capsule listing
func (s *CapsuleMarketplaceService) GetCapsule(id string) (*CapsuleListing, bool) {
	listing, ok := s.listings[id]
	return listing, ok
}

// CreateListing creates a new capsule listing
func (s *CapsuleMarketplaceService) CreateListing(listing *CapsuleListing) error {
	listing.ID = generateUUID()
	listing.CreatedAt = time.Now()
	listing.UpdatedAt = time.Now()
	listing.Downloads = 0
	listing.Rating = 0

	s.listings[listing.ID] = listing
	return nil
}

// UpdateListing updates an existing listing
func (s *CapsuleMarketplaceService) UpdateListing(id string, update *CapsuleListing) error {
	if _, ok := s.listings[id]; !ok {
		return ErrNotFound
	}

	listing := s.listings[id]
	listing.Description = update.Description
	listing.Tags = update.Tags
	listing.Capabilities = update.Capabilities
	listing.Status = update.Status
	listing.UpdatedAt = time.Now()

	return nil
}

// matchesFilter checks if a listing matches the filter
func (s *CapsuleMarketplaceService) matchesFilter(listing *CapsuleListing, filter CapsuleFilter) bool {
	if filter.Type != "" && listing.Type != filter.Type {
		return false
	}
	if filter.Status != "" && listing.Status != filter.Status {
		return false
	}
	if filter.Verified && !listing.Verified {
		return false
	}
	if filter.Author != "" && listing.Author != filter.Author {
		return false
	}
	return true
}

// CapsuleFilter represents search/filter criteria for capsules
type CapsuleFilter struct {
	Type     string
	Status   string
	Author   string
	Tags     []string
	Verified bool
	SortBy   string
	Page     int
	PageSize int
}
