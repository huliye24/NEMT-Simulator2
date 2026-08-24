// Package models provides data models for NEMT Gateway
package models

import "time"

// Strategy represents a trading strategy
type Strategy struct {
	ID           string         `json:"id" gorm:"primaryKey"`
	Name         string         `json:"name" gorm:"not null"`
	Author       string         `json:"author" gorm:"not null"`
	Type         StrategyType   `json:"type" gorm:"not null"`
	Code         string         `json:"code" gorm:"type:text"`
	SharpeRatio  float64        `json:"sharpe_ratio" gorm:"default:0"`
	MaxDrawdown  float64        `json:"max_drawdown" gorm:"default:0"`
	TotalTrades  int            `json:"total_trades" gorm:"default:0"`
	WinRate      float64        `json:"win_rate" gorm:"default:0"`
	Status       StrategyStatus `json:"status" gorm:"default:0"`
	CreatedAt    time.Time      `json:"created_at"`
	UpdatedAt    time.Time      `json:"updated_at"`
}

// TableName returns the table name
func (Strategy) TableName() string {
	return "strategies"
}

// StrategyType represents the type of strategy
type StrategyType int

const (
	TrendFollowing StrategyType = iota
	MeanReversion
	Arbitrage
	MarketMaking
	MLBased
)

// StrategyStatus represents the status of a strategy
type StrategyStatus int

const (
	StrategyDraft StrategyStatus = iota
	StrategyActive
	StrategyPaused
	StrategyArchived
)

// Capsule represents a trading capsule module
type Capsule struct {
	ID           string       `json:"id" gorm:"primaryKey"`
	Name         string       `json:"name" gorm:"not null"`
	Version      string       `json:"version" gorm:"not null"`
	Author       string       `json:"author" gorm:"not null"`
	Type         CapsuleType  `json:"type" gorm:"not null"`
	Code         string       `json:"code" gorm:"type:text"`
	Dependencies string       `json:"dependencies" gorm:"type:text"` // JSON array
	CreatedAt    time.Time    `json:"created_at"`
	UpdatedAt    time.Time    `json:"updated_at"`
}

// TableName returns the table name
func (Capsule) TableName() string {
	return "capsules"
}

// CapsuleType represents the type of capsule
type CapsuleType int

const (
	CapsuleMarket CapsuleType = iota
	CapsuleSignal
	CapsuleRisk
	CapsuleExecution
	CapsuleBrain
	CapsuleMonitor
)

// BacktestReport represents a backtest execution result
type BacktestReport struct {
	ID            string        `json:"id" gorm:"primaryKey"`
	StrategyID    string        `json:"strategy_id" gorm:"not null"`
	InitialCapital float64       `json:"initial_capital"`
	FinalEquity   float64       `json:"final_equity"`
	TotalPnL      float64       `json:"total_pnl"`
	ReturnPct     float64       `json:"return_pct"`
	MaxDrawdown   float64       `json:"max_drawdown"`
	SharpeRatio   float64       `json:"sharpe_ratio"`
	WinRate       float64       `json:"win_rate"`
	ProfitFactor  float64       `json:"profit_factor"`
	TotalTrades   int           `json:"total_trades"`
	TotalBars     int           `json:"total_bars"`
	Trades        []Trade       `json:"trades" gorm:"-"`
	EquityCurve   []EquityPoint `json:"equity_curve" gorm:"-"`
	CreatedAt     time.Time     `json:"created_at"`
}

// TableName returns the table name
func (BacktestReport) TableName() string {
	return "backtest_reports"
}

// Trade represents a single trade execution
type Trade struct {
	ID        int       `json:"id"`
	ReportID  string    `json:"report_id"`
	Side      string    `json:"side"`
	Price     float64   `json:"price"`
	Quantity  float64   `json:"quantity"`
	PnL       float64   `json:"pnl"`
	Timestamp time.Time `json:"timestamp"`
}

// TableName returns the table name
func (Trade) TableName() string {
	return "trades"
}

// EquityPoint represents an equity curve data point
type EquityPoint struct {
	ReportID  string    `json:"report_id"`
	Timestamp time.Time `json:"timestamp"`
	Equity    float64   `json:"equity"`
	Drawdown  float64   `json:"drawdown"`
}

// TableName returns the table name
func (EquityPoint) TableName() string {
	return "equity_points"
}

// MarketData represents a single bar of market data
type MarketData struct {
	ID        uint      `json:"-" gorm:"primaryKey;autoIncrement"`
	Symbol    string    `json:"symbol" gorm:"not null;index"`
	Timestamp time.Time `json:"timestamp" gorm:"not null;index:idx_symbol_time"`
	Open      float64   `json:"open"`
	High      float64   `json:"high"`
	Low       float64   `json:"low"`
	Close     float64   `json:"close"`
	Volume    float64   `json:"volume"`
}

// TableName returns the table name
func (MarketData) TableName() string {
	return "market_data"
}

// ============================================================================
// Request/Response Models
// ============================================================================

// CreateStrategyRequest represents a request to create a strategy
type CreateStrategyRequest struct {
	Name   string       `json:"name" binding:"required"`
	Author string       `json:"author"`
	Type   StrategyType `json:"type"`
	Code   string       `json:"code"`
}

// UpdateStrategyRequest represents a request to update a strategy
type UpdateStrategyRequest struct {
	Name   string       `json:"name"`
	Code   string       `json:"code"`
	Status StrategyStatus `json:"status"`
}

// RegisterCapsuleRequest represents a request to register a capsule
type RegisterCapsuleRequest struct {
	Name         string      `json:"name" binding:"required"`
	Version      string      `json:"version" binding:"required"`
	Author       string      `json:"author"`
	Type         CapsuleType `json:"type"`
	Code         string      `json:"code"`
	Dependencies []string    `json:"dependencies"`
}

// UpdateCapsuleRequest represents a request to update a capsule
type UpdateCapsuleRequest struct {
	Version      string   `json:"version"`
	Code         string   `json:"code"`
	Dependencies []string `json:"dependencies"`
}

// BacktestRequest represents a request to start a backtest
type BacktestRequest struct {
	StrategyID    string  `json:"strategy_id" binding:"required"`
	DataSource    string  `json:"data_source"`
	Symbol        string  `json:"symbol" binding:"required"`
	Interval      string  `json:"interval"`
	StartTime     int64   `json:"start_time"`
	EndTime       int64   `json:"end_time"`
	InitialCapital float64 `json:"initial_capital"`
}

// BacktestProgress represents backtest progress
type BacktestProgress struct {
	BacktestID  string  `json:"backtest_id"`
	Status      string  `json:"status"`
	Progress    float64 `json:"progress"`
	CurrentBar  int     `json:"current_bar"`
	TotalBars   int     `json:"total_bars"`
}
