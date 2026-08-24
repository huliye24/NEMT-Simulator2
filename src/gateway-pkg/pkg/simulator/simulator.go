// Package simulator provides the core simulation engine
package simulator

import (
	"context"
	"sync"
	"time"

	"github.com/nemt-lab/nemt-go/pkg/logger"
)

// ============================================================================
// Simulation Engine
// ============================================================================

// Config holds simulation configuration
type Config struct {
	InitialCapital float64
	Commission     float64 // per trade
	Slippage      float64 // percentage
	StartTime     time.Time
	EndTime       time.Time
	TimeStep      time.Duration
	DataSource    string
}

// DefaultConfig returns default simulation config
func DefaultConfig() *Config {
	return &Config{
		InitialCapital: 100000.0,
		Commission:     0.001,
		Slippage:       0.0005,
		StartTime:      time.Now().AddDate(0, -1, 0),
		EndTime:        time.Now(),
		TimeStep:       time.Minute,
		DataSource:     "backtest",
	}
}

// Engine is the main simulation engine
type Engine struct {
	cfg        *Config
	log        *logger.Logger
	ctx        context.Context
	cancel     context.CancelFunc
	state      EngineState
	portfolio  *Portfolio
	dataFeed   DataFeed
	handlers   []EventHandler
	mu         sync.RWMutex
}

// EngineState represents the engine state
type EngineState int

const (
	StateIdle EngineState = iota
	StateRunning
	StatePaused
	StateStopped
)

func (s EngineState) String() string {
	switch s {
	case StateIdle:
		return "idle"
	case StateRunning:
		return "running"
	case StatePaused:
		return "paused"
	case StateStopped:
		return "stopped"
	default:
		return "unknown"
	}
}

// NewEngine creates a new simulation engine
func NewEngine(cfg *Config, log *logger.Logger) *Engine {
	ctx, cancel := context.WithCancel(context.Background())
	return &Engine{
		cfg:       cfg,
		log:       log,
		ctx:       ctx,
		cancel:    cancel,
		state:     StateIdle,
		portfolio: NewPortfolio(cfg.InitialCapital),
		handlers:  make([]EventHandler, 0),
	}
}

// Start starts the simulation
func (e *Engine) Start(ctx context.Context) error {
	e.mu.Lock()
	if e.state == StateRunning {
		e.mu.Unlock()
		return ErrAlreadyRunning
	}
	e.state = StateRunning
	e.mu.Unlock()

	e.log.Info("Starting simulation", map[string]interface{}{
		"initial_capital": e.cfg.InitialCapital,
		"start_time":     e.cfg.StartTime,
		"end_time":       e.cfg.EndTime,
	})

	// Start data feed
	if e.dataFeed != nil {
		if err := e.dataFeed.Start(ctx); err != nil {
			return err
		}
	}

	// Run main loop
	go e.runLoop(ctx)

	return nil
}

// Stop stops the simulation
func (e *Engine) Stop() {
	e.mu.Lock()
	defer e.mu.Unlock()

	if e.state != StateStopped {
		e.state = StateStopped
		e.cancel()
		e.log.Info("Simulation stopped")
	}
}

// Pause pauses the simulation
func (e *Engine) Pause() {
	e.mu.Lock()
	defer e.mu.Unlock()

	if e.state == StateRunning {
		e.state = StatePaused
		e.log.Info("Simulation paused")
	}
}

// Resume resumes the simulation
func (e *Engine) Resume() {
	e.mu.Lock()
	defer e.mu.Unlock()

	if e.state == StatePaused {
		e.state = StateRunning
		e.log.Info("Simulation resumed")
	}
}

// GetState returns the current engine state
func (e *Engine) GetState() EngineState {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.state
}

// GetPortfolio returns the current portfolio
func (e *Engine) GetPortfolio() *Portfolio {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.portfolio
}

// SetDataFeed sets the data feed
func (e *Engine) SetDataFeed(feed DataFeed) {
	e.dataFeed = feed
}

// AddHandler adds an event handler
func (e *Engine) AddHandler(handler EventHandler) {
	e.handlers = append(e.handlers, handler)
}

// runLoop is the main simulation loop
func (e *Engine) runLoop(ctx context.Context) {
	currentTime := e.cfg.StartTime

	for currentTime.Before(e.cfg.EndTime) || currentTime.Equal(e.cfg.EndTime) {
		select {
		case <-ctx.Done():
			return
		default:
		}

		// Check if paused
		for e.GetState() == StatePaused {
			time.Sleep(100 * time.Millisecond)
			if e.GetState() == StateStopped {
				return
			}
		}

		// Get current market data
		data := e.getMarketData(currentTime)

		// Emit tick event
		e.emitEvent(Event{
			Type:      EventTick,
			Timestamp: currentTime,
			Data:      data,
		})

		// Update portfolio
		e.portfolio.Update(currentTime, data)

		// Advance time
		currentTime = currentTime.Add(e.cfg.TimeStep)

		// Small delay to prevent busy loop
		time.Sleep(10 * time.Millisecond)
	}

	e.mu.Lock()
	e.state = StateStopped
	e.mu.Unlock()

	e.emitEvent(Event{
		Type:      EventComplete,
		Timestamp: time.Now(),
		Data:      e.getResults(),
	})

	e.log.Info("Simulation complete", map[string]interface{}{
		"final_equity": e.portfolio.GetEquity(),
		"total_trades": e.portfolio.GetTradeCount(),
	})
}

// getMarketData returns market data for a given time
func (e *Engine) getMarketData(t time.Time) *MarketSnapshot {
	if e.dataFeed != nil {
		return e.dataFeed.GetSnapshot(t)
	}
	return nil
}

// getResults returns simulation results
func (e *Engine) getResults() *Results {
	return &Results{
		InitialCapital: e.cfg.InitialCapital,
		FinalEquity:    e.portfolio.GetEquity(),
		TotalReturn:    e.portfolio.GetTotalReturn(),
		MaxDrawdown:   e.portfolio.GetMaxDrawdown(),
		SharpeRatio:   e.portfolio.GetSharpeRatio(),
		TotalTrades:   e.portfolio.GetTradeCount(),
		WinRate:       e.portfolio.GetWinRate(),
		ProfitFactor:   e.portfolio.GetProfitFactor(),
		EquityCurve:   e.portfolio.GetEquityCurve(),
	}
}

// emitEvent emits an event to all handlers
func (e *Engine) emitEvent(event Event) {
	for _, handler := range e.handlers {
		handler.Handle(event)
	}
}

// Errors
var (
	ErrAlreadyRunning = &SimulationError{Code: "ALREADY_RUNNING", Message: "Simulation is already running"}
	ErrNotRunning     = &SimulationError{Code: "NOT_RUNNING", Message: "Simulation is not running"}
)

// SimulationError represents simulation errors
type SimulationError struct {
	Code    string
	Message string
}

func (e *SimulationError) Error() string {
	return e.Message
}

// ============================================================================
// Portfolio
// ============================================================================

// Portfolio tracks positions and equity
type Portfolio struct {
	initialCash float64
	cash       float64
	positions  map[string]*Position
	trades     []Trade
	equityCurve []EquityPoint
	mu         sync.RWMutex
}

// NewPortfolio creates a new portfolio
func NewPortfolio(initialCapital float64) *Portfolio {
	return &Portfolio{
		initialCash: initialCapital,
		cash:       initialCapital,
		positions:  make(map[string]*Position),
		trades:     make([]Trade, 0),
	}
}

// Position represents a position in a symbol
type Position struct {
	Symbol   string
	Quantity float64
	AvgCost  float64
}

// Trade represents a completed trade
type Trade struct {
	ID        string
	Symbol    string
	Side      string
	Price     float64
	Quantity  float64
	Commission float64
	Timestamp time.Time
}

// EquityPoint represents an equity curve point
type EquityPoint struct {
	Timestamp time.Time
	Equity   float64
	Drawdown float64
}

// GetEquity returns current portfolio equity
func (p *Portfolio) GetEquity() float64 {
	p.mu.RLock()
	defer p.mu.RUnlock()

	equity := p.cash
	for _, pos := range p.positions {
		equity += pos.Quantity * pos.AvgCost // Simplified
	}
	return equity
}

// GetTotalReturn returns total return percentage
func (p *Portfolio) GetTotalReturn() float64 {
	equity := p.GetEquity()
	return (equity - p.initialCash) / p.initialCash * 100
}

// GetMaxDrawdown returns maximum drawdown
func (p *Portfolio) GetMaxDrawdown() float64 {
	// Simplified - would calculate from equity curve
	return 0.0
}

// GetSharpeRatio returns Sharpe ratio
func (p *Portfolio) GetSharpeRatio() float64 {
	// Simplified - would calculate from returns
	return 0.0
}

// GetTradeCount returns total number of trades
func (p *Portfolio) GetTradeCount() int {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return len(p.trades)
}

// GetWinRate returns win rate
func (p *Portfolio) GetWinRate() float64 {
	// Simplified
	return 0.0
}

// GetProfitFactor returns profit factor
func (p *Portfolio) GetProfitFactor() float64 {
	// Simplified
	return 0.0
}

// GetEquityCurve returns equity curve
func (p *Portfolio) GetEquityCurve() []EquityPoint {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.equityCurve
}

// Update updates portfolio with new market data
func (p *Portfolio) Update(t time.Time, data *MarketSnapshot) {
	// Update equity curve
	equity := p.GetEquity()
	drawdown := p.GetMaxDrawdown()
	p.equityCurve = append(p.equityCurve, EquityPoint{
		Timestamp: t,
		Equity:    equity,
		Drawdown:  drawdown,
	})
}

// ============================================================================
// Data Feed
// ============================================================================

// DataFeed provides market data to the simulation
type DataFeed interface {
	Start(ctx context.Context) error
	Stop()
	GetSnapshot(t time.Time) *MarketSnapshot
}

// MarketSnapshot represents a snapshot of market data
type MarketSnapshot struct {
	Symbol    string
	Timestamp time.Time
	Open      float64
	High      float64
	Low       float64
	Close     float64
	Volume    float64
}

// ============================================================================
// Event System
// ============================================================================

// Event represents a simulation event
type Event struct {
	Type      EventType
	Timestamp time.Time
	Data      interface{}
}

// EventType represents event types
type EventType int

const (
	EventTick EventType = iota
	EventTrade
	EventOrder
	EventSignal
	EventComplete
	EventError
)

// EventHandler handles simulation events
type EventHandler interface {
	Handle(event Event)
}

// Results represents simulation results
type Results struct {
	InitialCapital float64       `json:"initial_capital"`
	FinalEquity   float64       `json:"final_equity"`
	TotalReturn   float64       `json:"total_return"`
	MaxDrawdown   float64       `json:"max_drawdown"`
	SharpeRatio   float64       `json:"sharpe_ratio"`
	TotalTrades   int           `json:"total_trades"`
	WinRate       float64       `json:"win_rate"`
	ProfitFactor  float64       `json:"profit_factor"`
	EquityCurve  []EquityPoint `json:"equity_curve"`
}

// ============================================================================
// Order System
// ============================================================================

// Order represents a trading order
type Order struct {
	ID        string
	Symbol    string
	Side      OrderSide
	Type      OrderType
	Quantity  float64
	Price     float64
	Status    OrderStatus
	Timestamp time.Time
	FilledAt  *time.Time
}

// OrderSide represents order side
type OrderSide int

const (
	OrderBuy OrderSide = iota
	OrderSell
)

// OrderType represents order type
type OrderType int

const (
	OrderMarket OrderType = iota
	OrderLimit
	OrderStop
)

// OrderStatus represents order status
type OrderStatus int

const (
	OrderPending OrderStatus = iota
	OrderFilled
	OrderCancelled
	OrderRejected
)
