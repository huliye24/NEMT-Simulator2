package discovery

import (
	"fmt"
	"os"
)

// Service endpoints for local development
// These are used when running in desktop mode with subprocesses

const (
	// Default HTTP port for the gateway service
	DefaultHTTPPort = 8080

	// Default gRPC port for the gateway service
	DefaultGRPCPort = 9090

	// Default gRPC port for the Python engine
	DefaultPythonPort = 50051

	// Localhost address
	Localhost = "localhost"
)

// Config holds local service discovery configuration
type Config struct {
	GatewayHTTP string
	GatewayGRPC string
	Python      string
}

// DefaultConfig returns the default local discovery configuration
func DefaultConfig() *Config {
	httpPort := os.Getenv("HTTP_PORT")
	if httpPort == "" {
		httpPort = fmt.Sprintf("%d", DefaultHTTPPort)
	}

	grpcPort := os.Getenv("GRPC_PORT")
	if grpcPort == "" {
		grpcPort = fmt.Sprintf("%d", DefaultGRPCPort)
	}

	pythonPort := os.Getenv("PYTHON_GRPC_PORT")
	if pythonPort == "" {
		pythonPort = fmt.Sprintf("%d", DefaultPythonPort)
	}

	return &Config{
		GatewayHTTP: fmt.Sprintf("http://%s:%s", Localhost, httpPort),
		GatewayGRPC: fmt.Sprintf("%s:%s", Localhost, grpcPort),
		Python:      fmt.Sprintf("%s:%s", Localhost, pythonPort),
	}
}

// GetGatewayHTTP returns the gateway HTTP endpoint
func (c *Config) GetGatewayHTTP() string {
	return c.GatewayHTTP
}

// GetGatewayGRPC returns the gateway gRPC endpoint
func (c *Config) GetGatewayGRPC() string {
	return c.GatewayGRPC
}

// GetPythonEndpoint returns the Python engine gRPC endpoint
func (c *Config) GetPythonEndpoint() string {
	return c.Python
}

// HealthEndpoint returns the health check endpoint
func (c *Config) HealthEndpoint() string {
	return c.GatewayHTTP + "/health"
}

// WebSocketEndpoint returns the WebSocket endpoint
func (c *Config) WebSocketEndpoint() string {
	return "ws://" + Localhost + ":" + os.Getenv("HTTP_PORT") + "/ws"
}
