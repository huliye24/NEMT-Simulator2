// Package gateway provides WebSocket handlers for real-time data
package gateway

import (
	"encoding/json"
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"github.com/nemt-lab/nemt-go/pkg/collector"
	"github.com/nemt-lab/nemt-go/pkg/common"
	"github.com/nemt-lab/nemt-go/pkg/logger"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for development
	},
}

// WebSocketHandler handles WebSocket connections
type WebSocketHandler struct {
	log       *logger.Logger
	collector *collector.Collector
	sessions  map[string]*wsSession
	mu        sync.RWMutex
}

type wsSession struct {
	ID      string
	Symbols []string
	Conn    *websocket.Conn
	Send    chan []byte
}

// NewWebSocketHandler creates a new WebSocket handler
func NewWebSocketHandler(log *logger.Logger, col *collector.Collector) *WebSocketHandler {
	return &WebSocketHandler{
		log:       log,
		collector: col,
		sessions:  make(map[string]*wsSession),
	}
}

// Handle handles WebSocket connections
func (h *WebSocketHandler) Handle(c *gin.Context) {
	// Upgrade to WebSocket
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		h.log.Error("WebSocket upgrade failed", err, nil)
		return
	}

	// Create session
	session := &wsSession{
		ID:      uuid.New().String(),
		Symbols: []string{},
		Conn:    conn,
		Send:    make(chan []byte, 256),
	}

	h.mu.Lock()
	h.sessions[session.ID] = session
	h.mu.Unlock()

	h.log.Info("WebSocket connected", map[string]interface{}{
		"session_id": session.ID,
	})

	// Register with collector
	h.collector.Subscribe(&collector.Subscriber{
		ID:   session.ID,
		Conn: conn,
	})

	// Start read/write goroutines
	go h.writePump(session)
	go h.readPump(session)
}

// readPump handles incoming messages
func (h *WebSocketHandler) readPump(session *wsSession) {
	defer func() {
		h.cleanup(session)
	}()

	for {
		_, message, err := session.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				h.log.Warn("WebSocket read error", map[string]interface{}{
					"session_id": session.ID,
					"error":      err.Error(),
				})
			}
			break
		}

		// Parse message
		var msg WebSocketMessage
		if err := json.Unmarshal(message, &msg); err != nil {
			h.sendError(session, "INVALID_MESSAGE", "Invalid message format")
			continue
		}

		h.handleMessage(session, &msg)
	}
}

// writePump handles outgoing messages
func (h *WebSocketHandler) writePump(session *wsSession) {
	defer session.Conn.Close()

	for {
		select {
		case message, ok := <-session.Send:
			if !ok {
				session.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := session.Conn.WriteMessage(websocket.TextMessage, message); err != nil {
				return
			}
		}
	}
}

// handleMessage handles incoming WebSocket messages
func (h *WebSocketHandler) handleMessage(session *wsSession, msg *WebSocketMessage) {
	switch msg.Type {
	case "subscribe":
		h.handleSubscribe(session, msg)
	case "unsubscribe":
		h.handleUnsubscribe(session, msg)
	case "ping":
		h.handlePing(session)
	default:
		h.sendError(session, "UNKNOWN_MESSAGE", "Unknown message type")
	}
}

// handleSubscribe handles subscribe requests
func (h *WebSocketHandler) handleSubscribe(session *wsSession, msg *WebSocketMessage) {
	if msg.Symbols == nil || len(msg.Symbols) == 0 {
		h.sendError(session, "INVALID_REQUEST", "Symbols required")
		return
	}

	session.Symbols = append(session.Symbols, msg.Symbols...)

	// Subscribe to collector
	h.collector.Subscribe(&collector.Subscriber{
		ID:      session.ID,
		Symbols: msg.Symbols,
		Conn:    session.Conn,
		Send:    session.Send,
	})

	h.log.Info("Subscribed to symbols", map[string]interface{}{
		"session_id": session.ID,
		"symbols":    msg.Symbols,
	})

	h.sendMessage(session, "subscribed", map[string]interface{}{
		"symbols": msg.Symbols,
	})
}

// handleUnsubscribe handles unsubscribe requests
func (h *WebSocketHandler) handleUnsubscribe(session *wsSession, msg *WebSocketMessage) {
	if msg.Symbols == nil || len(msg.Symbols) == 0 {
		h.sendError(session, "INVALID_REQUEST", "Symbols required")
		return
	}

	// Remove symbols from session
	newSymbols := make([]string, 0)
	for _, s := range session.Symbols {
		found := false
		for _, unsub := range msg.Symbols {
			if s == unsub {
				found = true
				break
			}
		}
		if !found {
			newSymbols = append(newSymbols, s)
		}
	}
	session.Symbols = newSymbols

	h.log.Info("Unsubscribed from symbols", map[string]interface{}{
		"session_id": session.ID,
		"symbols":    msg.Symbols,
	})

	h.sendMessage(session, "unsubscribed", map[string]interface{}{
		"symbols": msg.Symbols,
	})
}

// handlePing handles ping requests
func (h *WebSocketHandler) handlePing(session *wsSession) {
	h.sendMessage(session, "pong", map[string]interface{}{
		"timestamp": common.TimestampNow(),
	})
}

// sendMessage sends a message to a session
func (h *WebSocketHandler) sendMessage(session *wsSession, msgType string, data interface{}) {
	msg := WebSocketOutMessage{
		Type: msgType,
		Data: data,
	}
	payload, _ := json.Marshal(msg)
	select {
	case session.Send <- payload:
	default:
	}
}

// sendError sends an error message
func (h *WebSocketHandler) sendError(session *wsSession, code, message string) {
	h.sendMessage(session, "error", map[string]interface{}{
		"code":    code,
		"message": message,
	})
}

// cleanup cleans up a session
func (h *WebSocketHandler) cleanup(session *wsSession) {
	h.mu.Lock()
	delete(h.sessions, session.ID)
	h.mu.Unlock()

	close(session.Send)

	h.collector.Unsubscribe(&collector.Subscriber{
		ID:   session.ID,
		Conn: session.Conn,
	})

	h.log.Info("WebSocket disconnected", map[string]interface{}{
		"session_id": session.ID,
	})
}

// GetSessionCount returns the number of active sessions
func (h *WebSocketHandler) GetSessionCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.sessions)
}

// WebSocketMessage represents an incoming WebSocket message
type WebSocketMessage struct {
	Type    string   `json:"type"`
	Symbols []string `json:"symbols,omitempty"`
	Data    any      `json:"data,omitempty"`
}

// WebSocketOutMessage represents an outgoing WebSocket message
type WebSocketOutMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}
