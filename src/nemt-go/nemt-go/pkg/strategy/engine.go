// Package strategy provides strategy execution engine
package strategy

import (
	"context"
	"sync"
	"time"

	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
)

// ============================================================================
// Strategy Engine
// ============================================================================

// Engine manages strategy execution
type Engine struct {
	log        *logger.Logger
	strategies map[string]*Strategy
	executors  map[string]*Executor
	mu         sync.RWMutex
	ctx        context.Context
	cancel     context.CancelFunc
}

// NewEngine creates a new strategy engine
func NewEngine(log *logger.Logger) *Engine {
	ctx, cancel := context.WithCancel(context.Background())
	return &Engine{
		log:       log,
		strategies: make(map[string]*Strategy),
		executors:  make(map[string]*Executor),
		ctx:        ctx,
		cancel:     cancel,
	}
}

// Register registers a strategy
func (e *Engine) Register(strategy *Strategy) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if _, exists := e.strategies[strategy.ID]; exists {
		return ErrStrategyExists
	}

	e.strategies[strategy.ID] = strategy
	e.log.Info("Strategy registered", map[string]interface{}{
		"id":   strategy.ID,
		"name": strategy.Name,
	})

	return nil
}

// Unregister unregisters a strategy
func (e *Engine) Unregister(id string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if _, exists := e.strategies[id]; !exists {
		return ErrStrategyNotFound
	}

	// Stop executor if running
	if exec, exists := e.executors[id]; exists {
		exec.Stop()
		delete(e.executors, id)
	}

	delete(e.strategies, id)
	return nil
}

// Get retrieves a strategy
func (e *Engine) Get(id string) (*Strategy, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	strategy, ok := e.strategies[id]
	return strategy, ok
}

// List returns all strategies
func (e *Engine) List() []*Strategy {
	e.mu.RLock()
	defer e.mu.RUnlock()

	strategies := make([]*Strategy, 0, len(e.strategies))
	for _, s := range e.strategies {
		strategies = append(strategies, s)
	}
	return strategies
}

// Start starts a strategy
func (e *Engine) Start(id string, feed MarketFeed) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	strategy, exists := e.strategies[id]
	if !exists {
		return ErrStrategyNotFound
	}

	if _, running := e.executors[id]; running {
		return ErrStrategyRunning
	}

	executor := NewExecutor(strategy, feed, e.log)
	e.executors[id] = executor

	go executor.Run(e.ctx)

	e.log.Info("Strategy started", map[string]interface{}{
		"id":   id,
		"name": strategy.Name,
	})

	return nil
}

// Stop stops a strategy
func (e *Engine) Stop(id string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	executor, exists := e.executors[id]
	if !exists {
		return ErrStrategyNotRunning
	}

	executor.Stop()
	delete(e.executors, id)

	e.log.Info("Strategy stopped", map[string]interface{}{
		"id": id,
	})

	return nil
}

// StopAll stops all strategies
func (e *Engine) StopAll() {
	e.mu.Lock()
	defer e.mu.Unlock()

	for id, executor := range e.executors {
		executor.Stop()
		delete(e.executors, id)
	}
}

// IsRunning checks if a strategy is running
func (e *Engine) IsRunning(id string) bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	_, exists := e.executors[id]
	return exists
}

// Close closes the engine
func (e *Engine) Close() {
	e.StopAll()
	e.cancel()
}

// Errors
var (
	ErrStrategyExists   = &StrategyError{Code: "STRATEGY_EXISTS", Message: "Strategy already exists"}
	ErrStrategyNotFound = &StrategyError{Code: "STRATEGY_NOT_FOUND", Message: "Strategy not found"}
	ErrStrategyRunning  = &StrategyError{Code: "STRATEGY_RUNNING", Message: "Strategy is already running"}
	ErrStrategyNotRunning = &StrategyError{Code: "STRATEGY_NOT_RUNNING", Message: "Strategy is not running"}
)

// StrategyError represents strategy errors
type StrategyError struct {
	Code    string
	Message string
}

func (e *StrategyError) Error() string {
	return e.Message
}

// ============================================================================
// Strategy
// ============================================================================

// Strategy represents a trading strategy
type Strategy struct {
	ID          string          `json:"id"`
	Name        string          `json:"name"`
	Author      string          `json:"author"`
	Type        StrategyType    `json:"type"`
	Code        string          `json:"code"`
	Parameters  StrategyParams  `json:"parameters"`
	RiskParams  RiskParams      `json:"risk_params"`
	Status      StrategyStatus   `json:"status"`
	Metrics     StrategyMetrics `json:"metrics"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

// StrategyType represents strategy types
type StrategyType string

const (
	TypeTrendFollowing StrategyType = "trend_following"
	TypeMeanReversion StrategyType = "mean_reversion"
	TypeArbitrage    StrategyType = "arbitrage"
	TypeMarketMaking StrategyType = "market_making"
	TypeMLBased      StrategyType = "ml_based"
)

// StrategyStatus represents strategy status
type StrategyStatus string

const (
	StatusDraft    StrategyStatus = "draft"
	StatusActive   StrategyStatus = "active"
	StatusPaused   StrategyStatus = "paused"
	StatusArchived StrategyStatus = "archived"
)

// StrategyParams represents strategy parameters
type StrategyParams map[string]interface{}

// RiskParams represents risk management parameters
type RiskParams struct {
	MaxPositionSize  float64 `json:"max_position_size"`
	MaxDrawdown      float64 `json:"max_drawdown"`
	MaxDailyLoss     float64 `json:"max_daily_loss"`
	StopLoss         float64 `json:"stop_loss"`
	TakeProfit       float64 `json:"take_profit"`
}

// StrategyMetrics represents strategy performance metrics
type StrategyMetrics struct {
	SharpeRatio   float64 `json:"sharpe_ratio"`
	MaxDrawdown  float64 `json:"max_drawdown"`
	TotalTrades  int     `json:"total_trades"`
	WinRate      float64 `json:"win_rate"`
	ProfitFactor float64 `json:"profit_factor"`
	AnnualReturn float64 `json:"annual_return"`
}

// ============================================================================
// Executor
// ============================================================================

// Executor executes a strategy
type Executor struct {
	strategy *Strategy
	feed     MarketFeed
	log      *logger.Logger
	signals  chan *Signal
	running  bool
	mu       sync.RWMutex
}

// NewExecutor creates a new executor
func NewExecutor(strategy *Strategy, feed MarketFeed, log *logger.Logger) *Executor {
	return &Executor{
		strategy: strategy,
		feed:     feed,
		log:      log,
		signals:  make(chan *Signal, 100),
		running:  false,
	}
}

// Run starts strategy execution
func (e *Executor) Run(ctx context.Context) {
	e.mu.Lock()
	e.running = true
	e.mu.Unlock()

	e.log.Info("Executor starting", map[string]interface{}{
		"strategy_id": e.strategy.ID,
	})

	for {
		select {
		case <-ctx.Done():
			e.mu.Lock()
			e.running = false
			e.mu.Unlock()
			return
		case data := <-e.feed.Chan():
			signal := e.evaluate(data)
			if signal != nil {
				select {
				case e.signals <- signal:
				default:
					// Signal buffer full
				}
			}
		}
	}
}

// Stop stops strategy execution
func (e *Executor) Stop() {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.running = false
}

// IsRunning returns if executor is running
func (e *Executor) IsRunning() bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.running
}

// Signals returns the signal channel
func (e *Executor) Signals() <-chan *Signal {
	return e.signals
}

// evaluate evaluates the strategy and generates signals
func (e *Executor) evaluate(data *MarketData) *Signal {
	// Placeholder - in production, this would execute strategy code
	return nil
}

// ============================================================================
// Signal
// ============================================================================

// Signal represents a trading signal
type Signal struct {
	ID         string       `json:"id"`
	StrategyID string      `json:"strategy_id"`
	Symbol     string      `json:"symbol"`
	Action     SignalAction `json:"action"`
	Quantity   float64     `json:"quantity"`
	Price      float64     `json:"price"`
	Timestamp  time.Time   `json:"timestamp"`
	Confidence float64     `json:"confidence"`
	Reason     string      `json:"reason"`
}

// SignalAction represents signal actions
type SignalAction string

const (
	SignalBuy  SignalAction = "buy"
	SignalSell SignalAction = "sell"
	SignalHold SignalAction = "hold"
)

// ============================================================================
// Market Feed
// ============================================================================

// MarketFeed provides market data to strategies
type MarketFeed interface {
	Chan() <-chan *MarketData
}

// MemoryFeed is an in-memory market feed
type MemoryFeed struct {
	ch chan *MarketData
}

// NewMemoryFeed creates a new memory feed
func NewMemoryFeed() *MemoryFeed {
	return &MemoryFeed{
		ch: make(chan *MarketData, 1000),
	}
}

// Chan returns the channel
func (f *MemoryFeed) Chan() <-chan *MarketData {
	return f.ch
}

// Send sends market data
func (f *MemoryFeed) Send(data *MarketData) {
	select {
	case f.ch <- data:
	default:
		// Channel full
	}
}

// ============================================================================
// Signal Generator
// ============================================================================

// SignalGenerator generates trading signals
type SignalGenerator struct {
	log *logger.Logger
}

// NewSignalGenerator creates a new signal generator
func NewSignalGenerator(log *logger.Logger) *SignalGenerator {
	return &SignalGenerator{log: log}
}

// Generate generates signals based on market data
func (g *SignalGenerator) Generate(data *MarketData, params StrategyParams) *Signal {
	// Placeholder for signal generation logic
	// In production, this would implement various technical indicators
	// and signal generation algorithms

	signal := &Signal{
		ID:         common.GenerateUUID(),
		Symbol:     data.Symbol,
		Price:      data.Close,
		Quantity:   1.0,
		Timestamp:  data.Timestamp,
		Confidence: 0.5,
	}

	// Simple momentum signal (placeholder)
	if data.Close > data.Open {
		signal.Action = SignalBuy
		signal.Reason = "Price momentum"
	} else if data.Close < data.Open {
		signal.Action = SignalSell
		signal.Reason = "Negative momentum"
	} else {
		signal.Action = SignalHold
		signal.Reason = "No signal"
	}

	return signal
}

// MarketData represents market data for strategy evaluation
type MarketData struct {
	Symbol    string
	Timestamp time.Time
	Open      float64
	High      float64
	Low       float64
	Close     float64
	Volume    float64
}
