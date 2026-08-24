// Package guider provides the guide interface for the evolution system
package guider

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ============================================================================
// Guide Interface
// ============================================================================

// Interface is the main guide interface for human-AI collaboration
type Interface struct {
	sessions   map[string]*Session
	evolution  *EvolutionGuide
	metrics    *MetricsCollector
	preferences *UserPreferences
	mu         sync.RWMutex
}

// Session represents a guide session
type Session struct {
	ID           string
	UserID       string
	StartedAt    time.Time
	LastActivity time.Time
	Context      *SessionContext
	History      []*Interaction
	State        SessionState
}

// SessionContext holds session context
type SessionContext struct {
	Goals        []string
	Constraints  []string
	CurrentPhase string
	Progress     float64
}

// Interaction represents a user-AI interaction
type Interaction struct {
	ID        string
	Type      InteractionType
	Content   string
	Timestamp time.Time
	Metadata  map[string]interface{}
}

// InteractionType represents interaction types
type InteractionType string

const (
	InteractionAsk    InteractionType = "ask"
	InteractionSuggest InteractionType = "suggest"
	InteractionConfirm InteractionType = "confirm"
	InteractionWarn   InteractionType = "warn"
	InteractionReport InteractionType = "report"
)

// SessionState represents session state
type SessionState string

const (
	StateActive   SessionState = "active"
	StatePaused   SessionState = "paused"
	StateComplete SessionState = "complete"
)

// UserPreferences holds user preferences
type UserPreferences struct {
	Verbose      bool
	Notifications bool
	AutoConfirm  bool
	ReviewMode   bool
}

// MetricsCollector collects guide metrics
type MetricsCollector struct {
	InteractionsTotal int
	SuggestionsAccepted int
	SuggestionsRejected int
	AvgResponseTime   time.Duration
}

// EvolutionGuide provides evolution guidance
type EvolutionGuide struct {
	phases   []*Phase
	current  int
	strategies map[string]*GuidanceStrategy
}

// Phase represents an evolution phase
type Phase struct {
	ID          string
	Name        string
	Description string
	Status      PhaseStatus
	StartTime   time.Time
	EndTime     *time.Time
	Tasks       []*Task
}

// PhaseStatus represents phase status
type PhaseStatus string

const (
	PhasePending   PhaseStatus = "pending"
	PhaseActive   PhaseStatus = "active"
	PhaseComplete PhaseStatus = "complete"
	PhaseSkipped  PhaseStatus = "skipped"
)

// Task represents a guidance task
type Task struct {
	ID          string
	Name        string
	Description string
	Status      TaskStatus
	Priority    int
}

// TaskStatus represents task status
type TaskStatus string

const (
	TaskPending   TaskStatus = "pending"
	TaskInProgress TaskStatus = "in_progress"
	TaskComplete TaskStatus = "complete"
	TaskSkipped TaskStatus = "skipped"
)

// GuidanceStrategy represents a guidance strategy
type GuidanceStrategy struct {
	ID          string
	Name        string
	Description string
	Rules       []*GuidanceRule
	Active      bool
}

// GuidanceRule represents a guidance rule
type GuidanceRule struct {
	Condition   string
	Action      GuidanceAction
	Priority    int
}

// GuidanceAction represents guidance actions
type GuidanceAction struct {
	Type    ActionType
	Message string
	Command string
}

// ActionType represents action types
type ActionType string

const (
	ActionSuggest ActionType = "suggest"
	ActionWarn   ActionType = "warn"
	ActionBlock ActionType = "block"
	ActionHelp  ActionType = "help"
)

// NewInterface creates a new guide interface
func NewInterface() *Interface {
	return &Interface{
		sessions:   make(map[string]*Session),
		evolution:  NewEvolutionGuide(),
		metrics:    &MetricsCollector{},
		preferences: &UserPreferences{
			Verbose:       true,
			Notifications: true,
		},
	}
}

// CreateSession creates a new guide session
func (i *Interface) CreateSession(userID string) (*Session, error) {
	i.mu.Lock()
	defer i.mu.Unlock()

	session := &Session{
		ID:           uuid.New().String(),
		UserID:       userID,
		StartedAt:    time.Now(),
		LastActivity: time.Now(),
		Context: &SessionContext{
			Goals:        make([]string, 0),
			Constraints:  make([]string, 0),
			CurrentPhase: "initialization",
			Progress:     0,
		},
		History: make([]*Interaction, 0),
		State:   StateActive,
	}

	i.sessions[session.ID] = session
	return session, nil
}

// EndSession ends a guide session
func (i *Interface) EndSession(sessionID string) error {
	i.mu.Lock()
	defer i.mu.Unlock()

	session, ok := i.sessions[sessionID]
	if !ok {
		return fmt.Errorf("session %s not found", sessionID)
	}

	session.State = StateComplete
	return nil
}

// GetSession returns a session by ID
func (i *Interface) GetSession(sessionID string) (*Session, bool) {
	i.mu.RLock()
	defer i.mu.RUnlock()
	session, ok := i.sessions[sessionID]
	return session, ok
}

// Guide provides guidance for an action
func (i *Interface) Guide(ctx context.Context, sessionID string, action string) (*Guidance, error) {
	i.mu.Lock()
	defer i.mu.Unlock()

	session, ok := i.sessions[sessionID]
	if !ok {
		return nil, fmt.Errorf("session not found")
	}

	session.LastActivity = time.Now()

	guidance := &Guidance{
		ID:        uuid.New().String(),
		Action:    action,
		Timestamp: time.Now(),
		Messages:  make([]string, 0),
		Commands:  make([]string, 0),
	}

	// Apply guidance rules
	for _, strategy := range i.evolution.strategies {
		if strategy.Active {
			for _, rule := range strategy.Rules {
				if rule.Condition == action {
					switch rule.Action.Type {
					case ActionSuggest:
						guidance.Messages = append(guidance.Messages, rule.Action.Message)
					case ActionWarn:
						guidance.Messages = append(guidance.Messages, "⚠️ "+rule.Action.Message)
					case ActionBlock:
						guidance.Blocked = true
						guidance.Messages = append(guidance.Messages, "🚫 "+rule.Action.Message)
					}
					if rule.Action.Command != "" {
						guidance.Commands = append(guidance.Commands, rule.Action.Command)
					}
				}
			}
		}
	}

	// Record interaction
	interaction := &Interaction{
		ID:        uuid.New().String(),
		Type:      InteractionAsk,
		Content:   action,
		Timestamp: time.Now(),
	}
	session.History = append(session.History, interaction)

	return guidance, nil
}

// Suggest provides suggestions
func (i *Interface) Suggest(ctx context.Context, sessionID string, context string) ([]*Suggestion, error) {
	i.mu.Lock()
	defer i.mu.Unlock()

	suggestions := make([]*Suggestion, 0)

	// Generate context-aware suggestions
	switch context {
	case "code":
		suggestions = append(suggestions, &Suggestion{
			ID:          uuid.New().String(),
			Type:        SuggestionTypeImprove,
			Title:       "Code Quality",
			Description: "Consider adding error handling",
			Priority:    1,
		})
	case "architecture":
		suggestions = append(suggestions, &Suggestion{
			ID:          uuid.New().String(),
			Type:        SuggestionTypeOptimize,
			Title:       "Architecture Review",
			Description: "Module boundaries could be improved",
			Priority:    2,
		})
	}

	return suggestions, nil
}

// Report generates a progress report
func (i *Interface) Report(ctx context.Context, sessionID string) (*Report, error) {
	i.mu.RLock()
	defer i.mu.RUnlock()

	session, ok := i.sessions[sessionID]
	if !ok {
		return nil, fmt.Errorf("session not found")
	}

	return &Report{
		ID:         uuid.New().String(),
		SessionID:  sessionID,
		GeneratedAt: time.Now(),
		Progress:   session.Context.Progress,
		Phase:      session.Context.CurrentPhase,
		Metrics:    i.metrics,
		History:    session.History,
	}, nil
}

// ============================================================================
// Supporting Types
// ============================================================================

// Guidance represents guidance for an action
type Guidance struct {
	ID        string
	Action    string
	Timestamp time.Time
	Messages  []string
	Commands  []string
	Blocked   bool
}

// Suggestion represents a suggestion
type Suggestion struct {
	ID          string
	Type        SuggestionType
	Title       string
	Description string
	Priority    int
}

// SuggestionType represents suggestion types
type SuggestionType string

const (
	SuggestionTypeImprove SuggestionType = "improve"
	SuggestionTypeOptimize SuggestionType = "optimize"
	SuggestionTypeSecurity SuggestionType = "security"
	SuggestionTypeRefactor SuggestionType = "refactor"
)

// Report represents a progress report
type Report struct {
	ID         string
	SessionID  string
	GeneratedAt time.Time
	Progress   float64
	Phase      string
	Metrics    *MetricsCollector
	History    []*Interaction
}

// NewEvolutionGuide creates a new evolution guide
func NewEvolutionGuide() *EvolutionGuide {
	return &EvolutionGuide{
		phases:   make([]*Phase, 0),
		current:  0,
		strategies: map[string]*GuidanceStrategy{
			"default": {
				ID:       "default",
				Name:     "Default Strategy",
				Active:   true,
				Rules: []*GuidanceRule{
					{
						Condition: "create_file",
						Action: GuidanceAction{
							Type:    ActionSuggest,
							Message: "Consider adding documentation",
						},
						Priority: 1,
					},
					{
						Condition: "delete_file",
						Action: GuidanceAction{
							Type:    ActionWarn,
							Message: "This action cannot be undone",
						},
						Priority: 2,
					},
				},
			},
		},
	}
}

// SetPhase sets the current phase
func (g *EvolutionGuide) SetPhase(phaseID string) error {
	for i, phase := range g.phases {
		if phase.ID == phaseID {
			g.current = i
			return nil
		}
	}
	return fmt.Errorf("phase %s not found", phaseID)
}

// GetCurrentPhase returns the current phase
func (g *EvolutionGuide) GetCurrentPhase() *Phase {
	if g.current < len(g.phases) {
		return g.phases[g.current]
	}
	return nil
}
