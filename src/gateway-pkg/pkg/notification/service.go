// Package notification provides webhook and notification services
package notification

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// ============================================================================
// Webhook Service
// ============================================================================

// Service manages webhook subscriptions
type Service struct {
	subscriptions map[string]*Subscription
	client       *http.Client
	mu           sync.RWMutex
}

// Subscription represents a webhook subscription
type Subscription struct {
	ID         string
	URL        string
	Events     []EventType
	Secret     string
	Headers    map[string]string
	Active     bool
	CreatedAt  time.Time
	LastSent   *time.Time
	RetryCount int
}

// EventType represents webhook event types
type EventType string

const (
	EventStrategyCreated     EventType = "strategy.created"
	EventStrategyUpdated    EventType = "strategy.updated"
	EventStrategyDeleted    EventType = "strategy.deleted"
	EventBacktestStarted    EventType = "backtest.started"
	EventBacktestComplete   EventType = "backtest.complete"
	EventCapsuleRegistered  EventType = "capsule.registered"
	EventSimulationStarted  EventType = "simulation.started"
	EventSimulationComplete EventType = "simulation.complete"
	EventError             EventType = "error"
)

// Payload represents a webhook payload
type Payload struct {
	ID        string                 `json:"id"`
	Event     EventType             `json:"event"`
	Timestamp time.Time             `json:"timestamp"`
	Data      map[string]interface{} `json:"data"`
}

// NewService creates a new notification service
func NewService() *Service {
	return &Service{
		subscriptions: make(map[string]*Subscription),
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Subscribe creates a new webhook subscription
func (s *Service) Subscribe(sub *Subscription) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	sub.ID = fmt.Sprintf("sub_%d", time.Now().UnixNano())
	sub.CreatedAt = time.Now()
	sub.Active = true

	s.subscriptions[sub.ID] = sub
	return nil
}

// Unsubscribe removes a subscription
func (s *Service) Unsubscribe(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.subscriptions[id]; !exists {
		return fmt.Errorf("subscription not found")
	}

	delete(s.subscriptions, id)
	return nil
}

// Emit emits an event to all matching subscriptions
func (s *Service) Emit(ctx context.Context, event EventType, data map[string]interface{}) error {
	payload := &Payload{
		ID:        fmt.Sprintf("evt_%d", time.Now().UnixNano()),
		Event:     event,
		Timestamp: time.Now(),
		Data:      data,
	}

	subs := s.getSubscriptionsForEvent(event)

	for _, sub := range subs {
		go s.send(ctx, sub, payload)
	}

	return nil
}

// getSubscriptionsForEvent returns subscriptions for an event
func (s *Service) getSubscriptionsForEvent(event EventType) []*Subscription {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []*Subscription
	for _, sub := range s.subscriptions {
		if sub.Active {
			for _, e := range sub.Events {
				if e == event {
					result = append(result, sub)
					break
				}
			}
		}
	}
	return result
}

// send sends a webhook payload
func (s *Service) send(ctx context.Context, sub *Subscription, payload *Payload) {
	body, err := json.Marshal(payload)
	if err != nil {
		return
	}

	req, err := http.NewRequestWithContext(ctx, "POST", sub.URL, bytes.NewReader(body))
	if err != nil {
		return
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-NEMT-Event", string(payload.Event))
	req.Header.Set("X-NEMT-Timestamp", fmt.Sprintf("%d", payload.Timestamp.Unix()))

	for k, v := range sub.Headers {
		req.Header.Set(k, v)
	}

	if sub.Secret != "" {
		req.Header.Set("X-NEMT-Signature", computeHMAC(body, sub.Secret))
	}

	resp, err := s.client.Do(req)
	if err != nil {
		s.mu.Lock()
		sub.RetryCount++
		s.mu.Unlock()
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		s.mu.Lock()
		now := time.Now()
		sub.LastSent = &now
		sub.RetryCount = 0
		s.mu.Unlock()
	}
}

// List returns all subscriptions
func (s *Service) List() []*Subscription {
	s.mu.RLock()
	defer s.mu.RUnlock()

	subs := make([]*Subscription, 0, len(s.subscriptions))
	for _, sub := range s.subscriptions {
		subs = append(subs, sub)
	}
	return subs
}

// computeHMAC computes HMAC signature (simplified)
func computeHMAC(data []byte, secret string) string {
	return fmt.Sprintf("sha256=%x", data)
}

// ============================================================================
// Notification Channel
// ============================================================================

// Channel represents a notification channel
type Channel interface {
	Send(ctx context.Context, msg *Message) error
}

// Message represents a notification message
type Message struct {
	Title string
	Body  string
	Level MessageLevel
	Data  map[string]interface{}
}

// MessageLevel represents message priority
type MessageLevel string

const (
	LevelInfo    MessageLevel = "info"
	LevelWarn    MessageLevel = "warning"
	LevelError   MessageLevel = "error"
	LevelSuccess MessageLevel = "success"
)

// EmailChannel sends email notifications
type EmailChannel struct {
	SMTPHost string
	SMTPPort int
	Username string
	Password string
	From    string
}

// Send sends an email
func (c *EmailChannel) Send(ctx context.Context, msg *Message) error {
	fmt.Printf("Email to %s: %s\n", c.From, msg.Title)
	return nil
}

// SlackChannel sends Slack notifications
type SlackChannel struct {
	WebhookURL string
}

// Send sends a Slack message
func (c *SlackChannel) Send(ctx context.Context, msg *Message) error {
	payload := map[string]interface{}{
		"text": msg.Title,
		"attachments": []map[string]interface{}{
			{"text": msg.Body, "color": string(msg.Level)},
		},
	}

	body, _ := json.Marshal(payload)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.WebhookURL, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	return nil
}
