// Package decision provides the state decision engine
package decision

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ============================================================================
// Decision Engine
// ============================================================================

// Engine is the core decision making engine
type Engine struct {
	states       map[string]*State
	rules       []*DecisionRule
	strategies  map[string]*Strategy
	evaluator   *Evaluator
	mu          sync.RWMutex
}

// State represents a system state
type State struct {
	ID          string
	Name        string
	Type        StateType
	Value       float64
	Metadata    map[string]interface{}
	Timestamp   time.Time
	Confidence  float64
	ParentID    string
	ChildrenIDs []string
}

// StateType represents the type of state
type StateType string

const (
	StateNormal   StateType = "normal"
	StateWarning  StateType = "warning"
	StateCritical StateType = "critical"
	StateUnknown  StateType = "unknown"
)

// DecisionRule represents a decision rule
type DecisionRule struct {
	ID          string
	Name        string
	Condition   *Condition
	Priority    int
	Actions     []*Action
	Constraints []string
	Enabled     bool
}

// Condition represents a decision condition
type Condition struct {
	Field    string
	Operator string
	Value    interface{}
}

// Action represents a decision action
type Action struct {
	Type     ActionType
	Target   string
	Params   map[string]interface{}
	Continue bool
}

// ActionType represents action types
type ActionType string

const (
	ActionNotify  ActionType = "notify"
	ActionScale   ActionType = "scale"
	ActionMigrate ActionType = "migrate"
	ActionRepair  ActionType = "repair"
	ActionAlert   ActionType = "alert"
	ActionLog     ActionType = "log"
)

// Strategy represents a decision strategy
type Strategy struct {
	ID          string
	Name        string
	Rules       []*DecisionRule
	Evaluator   *Evaluator
	Active      bool
	LastUpdated time.Time
}

// Evaluator evaluates states and generates decisions
type Evaluator struct {
	weights map[string]float64
}

// NewEngine creates a new decision engine
func NewEngine() *Engine {
	return &Engine{
		states:      make(map[string]*State),
		rules:       make([]*DecisionRule, 0),
		strategies:  make(map[string]*Strategy),
		evaluator:   NewEvaluator(),
	}
}

// RegisterState registers a new state
func (e *Engine) RegisterState(state *State) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	state.ID = uuid.New().String()
	state.Timestamp = time.Now()

	e.states[state.ID] = state
	return nil
}

// UpdateState updates an existing state
func (e *Engine) UpdateState(state *State) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if _, exists := e.states[state.ID]; !exists {
		return fmt.Errorf("state %s not found", state.ID)
	}

	state.Timestamp = time.Now()
	e.states[state.ID] = state
	return nil
}

// GetState returns a state by ID
func (e *Engine) GetState(id string) (*State, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	state, ok := e.states[id]
	return state, ok
}

// ListStates returns all states
func (e *Engine) ListStates() []*State {
	e.mu.RLock()
	defer e.mu.RUnlock()

	states := make([]*State, 0, len(e.states))
	for _, s := range e.states {
		states = append(states, s)
	}
	return states
}

// RegisterRule registers a decision rule
func (e *Engine) RegisterRule(rule *DecisionRule) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	rule.ID = uuid.New().String()
	rule.Enabled = true

	e.rules = append(e.rules, rule)
	return nil
}

// UnregisterRule removes a decision rule
func (e *Engine) UnregisterRule(id string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	for i, rule := range e.rules {
		if rule.ID == id {
			e.rules = append(e.rules[:i], e.rules[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("rule %s not found", id)
}

// Evaluate evaluates current state and returns decisions
func (e *Engine) Evaluate(ctx context.Context) ([]*Decision, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	decisions := make([]*Decision, 0)

	for _, state := range e.states {
		for _, rule := range e.rules {
			if !rule.Enabled {
				continue
			}

			if e.matchCondition(state, rule.Condition) {
				decision := &Decision{
					ID:        uuid.New().String(),
					StateID:   state.ID,
					RuleID:    rule.ID,
					Actions:   rule.Actions,
					Priority:  rule.Priority,
					Timestamp: time.Now(),
				}
				decisions = append(decisions, decision)

				if !rule.Actions[0].Continue {
					break
				}
			}
		}
	}

	return decisions, nil
}

// matchCondition checks if a state matches a condition
func (e *Engine) matchCondition(state *State, cond *Condition) bool {
	if cond == nil {
		return true
	}

	var fieldValue interface{}
	switch cond.Field {
	case "type":
		fieldValue = string(state.Type)
	case "value":
		fieldValue = state.Value
	case "confidence":
		fieldValue = state.Confidence
	default:
		if state.Metadata != nil {
			fieldValue = state.Metadata[cond.Field]
		}
	}

	switch cond.Operator {
	case "==":
		return fmt.Sprintf("%v", fieldValue) == fmt.Sprintf("%v", cond.Value)
	case "!=":
		return fmt.Sprintf("%v", fieldValue) != fmt.Sprintf("%v", cond.Value)
	case ">":
		if fv, ok := fieldValue.(float64); ok {
			if v, ok := cond.Value.(float64); ok {
				return fv > v
			}
		}
	case "<":
		if fv, ok := fieldValue.(float64); ok {
			if v, ok := cond.Value.(float64); ok {
				return fv < v
			}
		}
	case ">=":
		if fv, ok := fieldValue.(float64); ok {
			if v, ok := cond.Value.(float64); ok {
				return fv >= v
			}
		}
	case "<=":
		if fv, ok := fieldValue.(float64); ok {
			if v, ok := cond.Value.(float64); ok {
				return fv <= v
			}
		}
	}

	return false
}

// CreateStrategy creates a new decision strategy
func (e *Engine) CreateStrategy(name string, ruleIDs []string) (*Strategy, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	rules := make([]*DecisionRule, 0)
	for _, id := range ruleIDs {
		for _, rule := range e.rules {
			if rule.ID == id {
				rules = append(rules, rule)
				break
			}
		}
	}

	strategy := &Strategy{
		ID:          uuid.New().String(),
		Name:        name,
		Rules:       rules,
		Evaluator:   e.evaluator,
		Active:      true,
		LastUpdated: time.Now(),
	}

	e.strategies[strategy.ID] = strategy
	return strategy, nil
}

// ExecuteDecision executes a decision
func (e *Engine) ExecuteDecision(ctx context.Context, decision *Decision) error {
	for _, action := range decision.Actions {
		if err := e.executeAction(ctx, action); err != nil {
			return err
		}
	}
	return nil
}

// executeAction executes a single action
func (e *Engine) executeAction(ctx context.Context, action *Action) error {
	switch action.Type {
	case ActionNotify:
		fmt.Printf("Notification: %s\n", action.Target)
	case ActionScale:
		fmt.Printf("Scaling: %s with params %v\n", action.Target, action.Params)
	case ActionMigrate:
		fmt.Printf("Migrating: %s\n", action.Target)
	case ActionRepair:
		fmt.Printf("Repairing: %s\n", action.Target)
	case ActionAlert:
		fmt.Printf("Alert: %s\n", action.Target)
	case ActionLog:
		fmt.Printf("Log: %s\n", action.Target)
	}
	return nil
}

// ============================================================================
// Decision
// ============================================================================

// Decision represents a decision made by the engine
type Decision struct {
	ID        string
	StateID   string
	RuleID    string
	Actions   []*Action
	Priority  int
	Timestamp time.Time
	Executed  bool
}

// ============================================================================
// Evaluator
// ============================================================================

// NewEvaluator creates a new evaluator
func NewEvaluator() *Evaluator {
	return &Evaluator{
		weights: map[string]float64{
			"performance": 0.3,
			"reliability": 0.3,
			"cost":        0.2,
			"security":     0.2,
		},
	}
}

// EvaluateState evaluates a state and returns a score
func (ev *Evaluator) EvaluateState(state *State) float64 {
	score := 0.0

	switch state.Type {
	case StateNormal:
		score = 100.0
	case StateWarning:
		score = 50.0
	case StateCritical:
		score = 0.0
	default:
		score = 25.0
	}

	return score * state.Confidence
}

// CompareDecisions compares two decisions
func (ev *Evaluator) CompareDecisions(d1, d2 *Decision) int {
	if d1.Priority != d2.Priority {
		if d1.Priority > d2.Priority {
			return 1
		}
		return -1
	}
	return 0
}

// ============================================================================
// Policy Engine
// ============================================================================

// PolicyEngine manages decision policies
type PolicyEngine struct {
	policies map[string]*Policy
	engine   *Engine
	mu       sync.RWMutex
}

// Policy represents a decision policy
type Policy struct {
	ID          string
	Name        string
	Description string
	Conditions  []*PolicyCondition
	Decisions   []*Decision
	Priority    int
	Active      bool
}

// PolicyCondition represents a policy condition
type PolicyCondition struct {
	StateType  StateType
	MinValue   float64
	MaxValue   float64
	TimeWindow time.Duration
}

// NewPolicyEngine creates a new policy engine
func NewPolicyEngine(engine *Engine) *PolicyEngine {
	return &PolicyEngine{
		policies: make(map[string]*Policy),
		engine:   engine,
	}
}

// CreatePolicy creates a new policy
func (pe *PolicyEngine) CreatePolicy(name string, conditions []*PolicyCondition) (*Policy, error) {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	policy := &Policy{
		ID:          uuid.New().String(),
		Name:        name,
		Conditions:  conditions,
		Priority:    1,
		Active:      true,
	}

	pe.policies[policy.ID] = policy
	return policy, nil
}

// EvaluatePolicy evaluates a policy against current state
func (pe *PolicyEngine) EvaluatePolicy(ctx context.Context, policyID string) ([]*Decision, error) {
	pe.mu.RLock()
	policy, ok := pe.policies[policyID]
	pe.mu.RUnlock()

	if !ok {
		return nil, fmt.Errorf("policy %s not found", policyID)
	}

	states := pe.engine.ListStates()
	decisions := make([]*Decision, 0)

	for _, state := range states {
		for _, cond := range policy.Conditions {
			if pe.matchPolicyCondition(state, cond) {
				decision := &Decision{
					ID:        uuid.New().String(),
					StateID:   state.ID,
					Priority:  policy.Priority,
					Timestamp: time.Now(),
				}
				decisions = append(decisions, decision)
			}
		}
	}

	return decisions, nil
}

// matchPolicyCondition checks if a state matches a policy condition
func (pe *PolicyEngine) matchPolicyCondition(state *State, cond *PolicyCondition) bool {
	if state.Type != cond.StateType {
		return false
	}

	if cond.MinValue > 0 && state.Value < cond.MinValue {
		return false
	}

	if cond.MaxValue > 0 && state.Value > cond.MaxValue {
		return false
	}

	return true
}
