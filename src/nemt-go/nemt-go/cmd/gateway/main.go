// Package main is the entry point for NEMT Gateway
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/nemt-lab/nemt-go/pkg/cache"
	"github.com/nemt-lab/nemt-go/pkg/collector"
	"github.com/nemt-lab/nemt-go/pkg/config"
	"github.com/nemt-lab/nemt-go/pkg/datasource"
	"github.com/nemt-lab/nemt-go/pkg/gateway"
	"github.com/nemt-lab/nemt-go/pkg/grpcserver"
	"github.com/nemt-lab/nemt-go/pkg/ipc"
	"github.com/nemt-lab/nemt-go/pkg/logger"
	"github.com/nemt-lab/nemt-go/pkg/middleware"
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

	log.Info("Starting NEMT Gateway", map[string]interface{}{
		"http_port":       cfg.Server.HTTPPort,
		"grpc_port":       cfg.Server.GRPCPort,
		"python_endpoint": cfg.Gateway.PythonEndpoint,
	})

	// Initialize market data collector
	marketCollector := collector.NewCollector(log)
	if err := marketCollector.Start(); err != nil {
		log.Warn("Failed to start market collector", map[string]interface{}{
			"error": err.Error(),
		})
	}

	// Initialize COS data source
	var cosDS *datasource.COSDataSource
	if cfg.COS.Enabled {
		cosDS, err = datasource.NewCOSDataSource(datasource.COSConfig{
			Enabled:   cfg.COS.Enabled,
			SecretID:  cfg.COS.SecretID,
			SecretKey: cfg.COS.SecretKey,
			Bucket:    cfg.COS.Bucket,
			Region:    cfg.COS.Region,
		})
		if err != nil {
			log.Warn("Failed to initialize COS data source", map[string]interface{}{
				"error": err.Error(),
			})
		} else {
			log.Info("COS data source initialized", map[string]interface{}{
				"bucket": cfg.COS.Bucket,
				"region": cfg.COS.Region,
			})
		}
	}

	// Initialize IPC client for Python communication
	pythonIPC, err := ipc.NewClient(&ipc.Config{
		Address:  cfg.Gateway.PythonEndpoint,
		Timeout:  30 * time.Second,
		Protocol: "grpc",
	}, log)
	if err != nil {
		log.Warn("Failed to connect to Python backend", map[string]interface{}{
			"error": err.Error(),
		})
		// Continue without Python connection - gateway can work standalone
	}

	// Initialize handlers
	strategyHandler := gateway.NewStrategyHandler(log)
	capsuleHandler := gateway.NewCapsuleHandler(log)
	backtestHandler := gateway.NewBacktestHandler(log)
	marketHandler := gateway.NewMarketDataHandler(log, marketCollector)
	wsHandler := gateway.NewWebSocketHandler(log, marketCollector)

	// Set COS data source if available
	if cosDS != nil {
		marketHandler.SetCOSDataSource(cosDS)
	}

	// Initialize caches
	strategyCache := cache.NewStrategyCache(1000)
	capsuleCache := cache.NewCapsuleCache(500)
	marketCache := cache.NewMarketDataCache(10000)

	// Initialize gRPC server
	grpcServer := grpcserver.NewServer(cfg.Server.GRPCAddress(), log)

	// Setup Gin router
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()

	// Apply middleware
	router.Use(middleware.Recovery(log))
	router.Use(middleware.Logger(log))
	router.Use(middleware.RequestID())
	router.Use(middleware.CORS())
	router.Use(middleware.RateLimit(100, time.Minute))

	// Health check endpoints
	router.GET("/health", healthHandler)
	router.GET("/ready", readyHandler)
	router.GET("/metrics", metricsHandler(log, marketCollector))

	// WebSocket endpoint
	router.GET("/ws", wsHandler.Handle)

	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		// Strategy routes
		strategies := v1.Group("/strategies")
		{
			strategies.GET("", strategyHandler.List)
			strategies.GET("/:id", strategyHandler.Get)
			strategies.POST("", strategyHandler.Create)
			strategies.PUT("/:id", strategyHandler.Update)
			strategies.DELETE("/:id", strategyHandler.Delete)
			strategies.POST("/:id/clone", strategyHandler.Clone)
		}

		// Capsule routes
		capsules := v1.Group("/capsules")
		{
			capsules.GET("", capsuleHandler.List)
			capsules.GET("/:id", capsuleHandler.Get)
			capsules.POST("", capsuleHandler.Register)
			capsules.PUT("/:id", capsuleHandler.Update)
			capsules.DELETE("/:id", capsuleHandler.Delete)
			capsules.GET("/name/:name/versions", capsuleHandler.GetVersions)
		}

		// Backtest routes
		backtests := v1.Group("/backtest")
		{
			backtests.POST("", backtestHandler.Start)
			backtests.GET("", backtestHandler.List)
			backtests.GET("/:id", backtestHandler.Get)
			backtests.GET("/:id/progress", backtestHandler.GetProgress)
			backtests.GET("/:id/equity", backtestHandler.GetEquityCurve)
			backtests.GET("/:id/trades", backtestHandler.GetTrades)
			backtests.DELETE("/:id", backtestHandler.Cancel)
		}

		// Market data routes
		market := v1.Group("/market")
		{
			market.GET("/:symbol", marketHandler.Get)
			market.GET("/:symbol/latest", marketHandler.GetLatest)
			market.GET("/:symbol/subscribe", marketHandler.Subscribe)
			market.GET("/:symbol/ohlcv", marketHandler.GetOHLCV)
			market.GET("/symbols", marketHandler.GetSupportedSymbols)
			market.GET("/intervals", marketHandler.GetSupportedIntervals)
		}

		// COS data routes
		cos := v1.Group("/cos")
		{
			cos.GET("/index", marketHandler.GetCOSIndex)
			cos.GET("/health", marketHandler.COSHealthCheck)
			cos.POST("/cache/invalidate", marketHandler.InvalidateCOSCache)
		}
	}

	// Start cache cleanup goroutine
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		ticker := time.NewTicker(5 * time.Minute)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				strategyCache.Cleanup()
				capsuleCache.Cleanup()
				marketCache.Cleanup()
			}
		}
	}()

	// Create HTTP server
	srv := &http.Server{
		Addr:         cfg.Server.HTTPAddress(),
		Handler:      router,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
	}

	// Start server in goroutine
	go func() {
		log.Info("HTTP server starting", map[string]interface{}{
			"address": cfg.Server.HTTPAddress(),
		})
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("HTTP server failed", err, nil)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("Shutting down server...")

	// Graceful shutdown
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownPeriod)
	defer shutdownCancel()

	// Stop components
	marketCollector.Stop()
	grpcServer.Stop()
	if pythonIPC != nil {
		pythonIPC.Close()
	}

	// Stop HTTP server
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatal("Server forced to shutdown", err, nil)
	}

	log.Info("Server exited")
}

// ============================================================================
// Basic Handlers
// ============================================================================

func healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "nemt-gateway",
		"version": "1.0.0",
		"time":    time.Now().UTC().Format(time.RFC3339),
	})
}

func readyHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "ready",
		"time":   time.Now().UTC().Format(time.RFC3339),
	})
}

func metricsHandler(log *logger.Logger, col *collector.Collector) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":             "ok",
			"websocket_sessions":  col.GetTotalSubscribers(),
			"timestamp":           time.Now().UTC().Format(time.RFC3339),
		})
	}
}
