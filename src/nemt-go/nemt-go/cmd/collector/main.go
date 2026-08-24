// Package main is the entry point for NEMT Collector
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nemt-lab/nemt-go/pkg/config"
	"github.com/nemt-lab/nemt-go/pkg/logger"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load config: %v\n", err)
		os.Exit(1)
	}

	// Initialize logger
	log := logger.New(
		cfg.Logging.Level,
		cfg.Logging.Format,
		cfg.Logging.OutputPath,
	)

	log.Info("Starting NEMT Collector", map[string]interface{}{
		"redis_address": cfg.Redis.Address(),
	})

	// TODO: Implement WebSocket connection to exchange
	// TODO: Implement data parsing and normalization
	// TODO: Implement Redis publishing

	log.Info("Collector initialized", map[string]interface{}{
		"message": "Collector functionality pending implementation",
	})

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("Shutting down collector...")
	time.Sleep(100 * time.Millisecond)
	log.Info("Collector stopped")
}

// collector holds the collector state
type collector struct {
	cfg *config.Config
	log *logger.Logger
}

// connect establishes connection to data source
func (c *collector) connect(ctx context.Context) error {
	// TODO: Implement WebSocket connection
	return nil
}

// subscribe subscribes to market data
func (c *collector) subscribe(symbols []string) error {
	// TODO: Implement subscription management
	return nil
}

// handleMessage processes incoming messages
func (c *collector) handleMessage(data []byte) error {
	// TODO: Parse and normalize market data
	return nil
}

// publish publishes data to Redis
func (c *collector) publish(key string, data interface{}) error {
	// TODO: Implement Redis publish
	return nil
}
