// Package config provides configuration management for NEMT Gateway
package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the application
type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Redis    RedisConfig
	Logging  LoggingConfig
	Gateway  GatewayConfig
	COS      COSConfig
}

// ServerConfig holds HTTP/gRPC server configuration
type ServerConfig struct {
	Host            string
	HTTPPort       int
	GRPCPort       int
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	ShutdownPeriod time.Duration
}

// DatabaseConfig holds PostgreSQL configuration
type DatabaseConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	Database string
	MaxOpen  int
	MaxIdle  int
}

// RedisConfig holds Redis configuration
type RedisConfig struct {
	Host     string
	Port     int
	Password string
	DB       int
	PoolSize int
}

// LoggingConfig holds logging configuration
type LoggingConfig struct {
	Level      string
	Format     string
	OutputPath string
}

// GatewayConfig holds gateway-specific configuration
type GatewayConfig struct {
	PythonEndpoint   string
	CollectorEnabled bool
	CacheTTL         time.Duration
}

// COSConfig holds Tencent Cloud COS configuration
type COSConfig struct {
	Enabled   bool
	SecretID  string
	SecretKey string
	Bucket    string
	Region    string
	CacheTTL  time.Duration
}

// Default returns a default configuration
func Default() *Config {
	return &Config{
		Server: ServerConfig{
			Host:            "0.0.0.0",
			HTTPPort:        8080,
			GRPCPort:        9090,
			ReadTimeout:     30 * time.Second,
			WriteTimeout:    30 * time.Second,
			ShutdownPeriod:  10 * time.Second,
		},
		Database: DatabaseConfig{
			Host:     getEnv("DB_HOST", "localhost"),
			Port:     getEnvInt("DB_PORT", 5432),
			User:     getEnv("DB_USER", "nemt"),
			Password: getEnv("DB_PASSWORD", "nemt"),
			Database: getEnv("DB_NAME", "nemt"),
			MaxOpen:  25,
			MaxIdle:  5,
		},
		Redis: RedisConfig{
			Host:     getEnv("REDIS_HOST", "localhost"),
			Port:     getEnvInt("REDIS_PORT", 6379),
			Password: getEnv("REDIS_PASSWORD", ""),
			DB:       getEnvInt("REDIS_DB", 0),
			PoolSize: 10,
		},
		Logging: LoggingConfig{
			Level:      getEnv("LOG_LEVEL", "info"),
			Format:     getEnv("LOG_FORMAT", "json"),
			OutputPath: getEnv("LOG_PATH", "stdout"),
		},
		Gateway: GatewayConfig{
			PythonEndpoint:   getEnv("PYTHON_ENDPOINT", "localhost:50051"),
			CollectorEnabled: getEnvBool("COLLECTOR_ENABLED", false),
			CacheTTL:         getEnvDuration("CACHE_TTL", 5*time.Minute),
		},
		COS: COSConfig{
			Enabled:   getEnvBool("COS_ENABLED", false),
			SecretID:  getEnv("COS_SECRET_ID", ""),
			SecretKey: getEnv("COS_SECRET_KEY", ""),
			Bucket:    getEnv("COS_BUCKET", ""),
			Region:    getEnv("COS_REGION", "ap-guangzhou"),
			CacheTTL:  getEnvDuration("COS_CACHE_TTL", 5*time.Minute),
		},
	}
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	cfg := Default()

	// Validate required fields
	if cfg.Server.HTTPPort <= 0 || cfg.Server.HTTPPort > 65535 {
		return nil, fmt.Errorf("invalid HTTP port: %d", cfg.Server.HTTPPort)
	}
	if cfg.Server.GRPCPort <= 0 || cfg.Server.GRPCPort > 65535 {
		return nil, fmt.Errorf("invalid gRPC port: %d", cfg.Server.GRPCPort)
	}

	return cfg, nil
}

// DSN returns the PostgreSQL connection string
func (c *DatabaseConfig) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		c.Host, c.Port, c.User, c.Password, c.Database,
	)
}

// Address returns the Redis address
func (c *RedisConfig) Address() string {
	return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

// HTTPAddress returns the HTTP server address
func (c *ServerConfig) HTTPAddress() string {
	return fmt.Sprintf("%s:%d", c.Host, c.HTTPPort)
}

// GRPCAddress returns the gRPC server address
func (c *ServerConfig) GRPCAddress() string {
	return fmt.Sprintf("%s:%d", c.Host, c.GRPCPort)
}

// Helper functions for environment variables

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolVal, err := strconv.ParseBool(value); err == nil {
			return boolVal
		}
	}
	return defaultValue
}

func getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}
