// Package grpcclient provides gRPC client implementation
package grpcclient

import (
	"context"
	"time"

	"github.com/nemt-lab/nemt-go/pkg/logger"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Client represents a gRPC client for NEMT services
type Client struct {
	conn *grpc.ClientConn
	log  *logger.Logger
}

// Config holds client configuration
type Config struct {
	Address    string
	Timeout    time.Duration
	MaxRetries int
}

// DefaultConfig returns default client configuration
func DefaultConfig() *Config {
	return &Config{
		Address:    "localhost:50051",
		Timeout:    30 * time.Second,
		MaxRetries: 3,
	}
}

// NewClient creates a new gRPC client
func NewClient(cfg *Config, log *logger.Logger) (*Client, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	conn, err := grpc.DialContext(
		ctx,
		cfg.Address,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		log.Error("Failed to connect to gRPC server", err, map[string]interface{}{
			"address": cfg.Address,
		})
		return nil, err
	}

	log.Info("gRPC client connected", map[string]interface{}{
		"address": cfg.Address,
	})

	return &Client{
		conn: conn,
		log:  log,
	}, nil
}

// Close closes the client connection
func (c *Client) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// Conn returns the underlying gRPC connection
func (c *Client) Conn() *grpc.ClientConn {
	return c.conn
}

// ============================================================================
// Python Communication Client
// ============================================================================

// PythonClient communicates with Python backend
type PythonClient struct {
	client *Client
}

// NewPythonClient creates a client for Python communication
func NewPythonClient(address string, log *logger.Logger) (*PythonClient, error) {
	cfg := DefaultConfig()
	cfg.Address = address

	client, err := NewClient(cfg, log)
	if err != nil {
		return nil, err
	}

	return &PythonClient{client: client}, nil
}

// Close closes the Python client
func (c *PythonClient) Close() error {
	return c.client.Close()
}

// TODO: Implement Python-specific RPC calls
// These would call the Python gRPC service defined in proto/nemt.proto

/*
Example implementations:

// ExecuteStrategy executes a strategy via Python backend
func (c *PythonClient) ExecuteStrategy(ctx context.Context, strategyID string) (*StrategyResult, error) {
	// Call Python backend
	// proto := c.client.Conn()
	// client := proto.NewNEMTPythonClient(proto)
	// resp, err := client.ExecuteStrategy(ctx, &proto.ExecuteStrategyRequest{
	//     StrategyId: strategyID,
	// })
	return nil, nil
}

// StreamMarketData streams market data from Python backend
func (c *PythonClient) StreamMarketData(ctx context.Context, symbol string, interval string) (<-chan *MarketData, error) {
	// proto := c.client.Conn()
	// client := proto.NewNEMTPythonClient(proto)
	// stream, err := client.SubscribeMarketData(ctx, &proto.MarketDataRequest{
	//     Symbol:   symbol,
	//     Interval: interval,
	// })
	return nil, nil
}
*/

// StrategyResult represents strategy execution result
type StrategyResult struct {
	ID         string
	Status     string
	PnL        float64
	Sharpe     float64
	MaxDrawdown float64
}

// MarketData represents market data
type MarketData struct {
	Symbol    string
	Timestamp time.Time
	Open      float64
	High      float64
	Low       float64
	Close     float64
	Volume    float64
}
