// Package ipc provides IPC communication between Go and Python
package ipc

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"sync"
	"time"

	"github.com/nemt-lab/nemt-go/pkg/logger"
)

// Config holds IPC configuration
type Config struct {
	Address  string
	Timeout  time.Duration
	Protocol string // "stdio", "pipe", "grpc"
}

// DefaultConfig returns default IPC configuration
func DefaultConfig() *Config {
	return &Config{
		Address:  "localhost:50051",
		Timeout:  30 * time.Second,
		Protocol: "grpc",
	}
}

// Client provides IPC communication with Python backend
type Client struct {
	cfg       *Config
	log      *logger.Logger
	conn     net.Conn
	mu       sync.RWMutex
	ctx      context.Context
	cancel   context.CancelFunc
	requests chan *Request
	responses map[string]chan *Response
}

// Request represents an IPC request
type Request struct {
	ID      string      `json:"id"`
	Command string      `json:"command"`
	Args    interface{} `json:"args"`
	Timeout time.Duration
}

// Response represents an IPC response
type Response struct {
	ID     string      `json:"id"`
	Result interface{} `json:"result"`
	Error  *ErrorInfo  `json:"error,omitempty"`
}

// ErrorInfo represents an error
type ErrorInfo struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// NewClient creates a new IPC client
func NewClient(cfg *Config, log *logger.Logger) (*Client, error) {
	ctx, cancel := context.WithCancel(context.Background())

	client := &Client{
		cfg:       cfg,
		log:       log,
		ctx:       ctx,
		cancel:    cancel,
		requests:  make(chan *Request, 100),
		responses: make(map[string]chan *Response),
	}

	// Start request processor
	go client.processRequests()

	return client, nil
}

// Connect establishes connection to Python backend
func (c *Client) Connect() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	var err error
	c.conn, err = net.DialTimeout("tcp", c.cfg.Address, c.cfg.Timeout)
	if err != nil {
		c.log.Error("Failed to connect to Python backend", err, map[string]interface{}{
			"address": c.cfg.Address,
		})
		return err
	}

	c.log.Info("Connected to Python backend", map[string]interface{}{
		"address": c.cfg.Address,
	})

	// Start response reader
	go c.readResponses()

	return nil
}

// Close closes the IPC client
func (c *Client) Close() error {
	c.cancel()

	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn != nil {
		err := c.conn.Close()
		c.conn = nil
		return err
	}
	return nil
}

// Call sends a request and waits for response
func (c *Client) Call(ctx context.Context, command string, args interface{}) (*Response, error) {
	req := &Request{
		ID:      generateID(),
		Command: command,
		Args:    args,
		Timeout: c.cfg.Timeout,
	}

	// Create response channel
	respChan := make(chan *Response, 1)
	c.responses[req.ID] = respChan
	defer delete(c.responses, req.ID)

	// Send request
	select {
	case c.requests <- req:
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	// Wait for response
	select {
	case resp := <-respChan:
		return resp, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-c.ctx.Done():
		return nil, c.ctx.Err()
	}
}

// Execute executes a command and returns the result
func (c *Client) Execute(ctx context.Context, command string, args interface{}) (interface{}, error) {
	resp, err := c.Call(ctx, command, args)
	if err != nil {
		return nil, err
	}
	if resp.Error != nil {
		return nil, fmt.Errorf("%s: %s", resp.Error.Code, resp.Error.Message)
	}
	return resp.Result, nil
}

// processRequests processes outgoing requests
func (c *Client) processRequests() {
	for {
		select {
		case <-c.ctx.Done():
			return
		case req := <-c.requests:
			c.sendRequest(req)
		}
	}
}

// sendRequest sends a request to the connection
func (c *Client) sendRequest(req *Request) {
	c.mu.RLock()
	conn := c.conn
	c.mu.RUnlock()

	if conn == nil {
		c.responses[req.ID] <- &Response{
			ID: req.ID,
			Error: &ErrorInfo{
				Code:    "NOT_CONNECTED",
				Message: "Not connected to Python backend",
			},
		}
		return
	}

	data, _ := json.Marshal(req)
	_, err := conn.Write(append(data, '\n'))
	if err != nil {
		c.log.Error("Failed to send request", err, map[string]interface{}{
			"request_id": req.ID,
			"command":    req.Command,
		})
		c.responses[req.ID] <- &Response{
			ID: req.ID,
			Error: &ErrorInfo{
				Code:    "SEND_ERROR",
				Message: err.Error(),
			},
		}
	}
}

// readResponses reads responses from the connection
func (c *Client) readResponses() {
	reader := bufio.NewReader(c.conn)
	for {
		select {
		case <-c.ctx.Done():
			return
		default:
			data, err := reader.ReadBytes('\n')
			if err != nil {
				if err != io.EOF {
					c.log.Error("Failed to read response", err, nil)
				}
				return
			}

			var resp Response
			if err := json.Unmarshal(data, &resp); err != nil {
				c.log.Warn("Failed to parse response", map[string]interface{}{
					"error": err.Error(),
				})
				continue
			}

			// Send to response channel
			if ch, ok := c.responses[resp.ID]; ok {
				select {
				case ch <- &resp:
				default:
				}
			}
		}
	}
}

// ============================================================================
// Server (for Python to connect to)
// ============================================================================

// Server provides IPC server for Python to connect to
type Server struct {
	cfg     *Config
	log     *logger.Logger
	listener net.Listener
	handler RequestHandler
	ctx     context.Context
	cancel  context.CancelFunc
}

// RequestHandler handles incoming requests
type RequestHandler interface {
	HandleRequest(req *Request) *Response
}

// NewServer creates a new IPC server
func NewServer(cfg *Config, log *logger.Logger, handler RequestHandler) *Server {
	ctx, cancel := context.WithCancel(context.Background())
	return &Server{
		cfg:     cfg,
		log:     log,
		handler: handler,
		ctx:     ctx,
		cancel:  cancel,
	}
}

// Start starts the IPC server
func (s *Server) Start() error {
	var err error
	s.listener, err = net.Listen("tcp", s.cfg.Address)
	if err != nil {
		return err
	}

	s.log.Info("IPC server starting", map[string]interface{}{
		"address": s.cfg.Address,
	})

	go s.accept()

	return nil
}

// Stop stops the IPC server
func (s *Server) Stop() {
	s.cancel()
	if s.listener != nil {
		s.listener.Close()
	}
}

// accept accepts connections
func (s *Server) accept() {
	for {
		conn, err := s.listener.Accept()
		if err != nil {
			select {
			case <-s.ctx.Done():
				return
			default:
				s.log.Error("Failed to accept connection", err, nil)
				continue
			}
		}

		go s.handleConnection(conn)
	}
}

// handleConnection handles a single connection
func (s *Server) handleConnection(conn net.Conn) {
	defer conn.Close()

	s.log.Info("Python client connected", map[string]interface{}{
		"remote": conn.RemoteAddr().String(),
	})

	reader := bufio.NewReader(conn)
	for {
		data, err := reader.ReadBytes('\n')
		if err != nil {
			if err != io.EOF {
				s.log.Error("Failed to read request", err, nil)
			}
			return
		}

		var req Request
		if err := json.Unmarshal(data, &req); err != nil {
			s.log.Warn("Failed to parse request", map[string]interface{}{
				"error": err.Error(),
			})
			continue
		}

		// Handle request
		resp := s.handler.HandleRequest(&req)

		// Send response
		respData, _ := json.Marshal(resp)
		conn.Write(append(respData, '\n'))
	}
}

// ============================================================================
// Utility Functions
// ============================================================================

func generateID() string {
	return fmt.Sprintf("%d-%d", time.Now().UnixNano(), time.Now().UnixNano()%10000)
}
