package grpcpool

import (
	"context"
	"sync"
	"sync/atomic"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/connectivity"
	"google.golang.org/grpc/credentials/insecure"
)

// Config holds connection pool configuration
type Config struct {
	// Target address (e.g., "localhost:50051")
	Target string
	// Pool size (number of connections)
	PoolSize int
	// Connection timeout
	Timeout time.Duration
	// Health check interval
	HealthCheckInterval time.Duration
	// Max idle time before closing connection
	MaxIdleTime time.Duration
}

// DefaultConfig returns default pool configuration
func DefaultConfig(target string) *Config {
	return &Config{
		Target:              target,
		PoolSize:            10,
		Timeout:             5 * time.Second,
		HealthCheckInterval: 30 * time.Second,
		MaxIdleTime:         5 * time.Minute,
	}
}

// Pool manages a pool of gRPC connections
type Pool struct {
	config     *Config
	conns      []*grpc.ClientConn
	idx        atomic.Int64
	mu         sync.Mutex
	ctx        context.Context
	cancel     context.CancelFunc
	closed     atomic.Bool
	connCount  atomic.Int64
}

// NewPool creates a new connection pool
func NewPool(config *Config) (*Pool, error) {
	if config.PoolSize <= 0 {
		config.PoolSize = 10
	}

	ctx, cancel := context.WithCancel(context.Background())

	pool := &Pool{
		config: config,
		conns:  make([]*grpc.ClientConn, 0, config.PoolSize),
		ctx:    ctx,
		cancel: cancel,
	}

	// Initialize connections
	for i := 0; i < config.PoolSize; i++ {
		conn, err := pool.createConn()
		if err != nil {
			pool.Close()
			return nil, err
		}
		pool.conns = append(pool.conns, conn)
		atomic.AddInt64(&pool.connCount, 1)
	}

	// Start health checker
	go pool.healthChecker()

	return pool, nil
}

// createConn creates a new gRPC connection
func (p *Pool) createConn() (*grpc.ClientConn, error) {
	ctx, cancel := context.WithTimeout(p.ctx, p.config.Timeout)
	defer cancel()

	conn, err := grpc.DialContext(
		ctx,
		p.config.Target,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
		grpc.WithConnectParams(grpc.ConnectParams{
			BackoffMaxDelay:   5 * time.Second,
			MinConnectTimeout:  2 * time.Second,
		}),
	)

	if err != nil {
		return nil, err
	}

	return conn, nil
}

// Get returns a connection from the pool (round-robin)
func (p *Pool) Get() (*grpc.ClientConn, error) {
	if p.closed.Load() {
		return nil, ErrPoolClosed
	}

	// Simple round-robin selection
	idx := int(p.idx.Add(1) - 1)
	conn := p.conns[idx%len(p.conns)]

	// Check connection state
	state := conn.GetState()
	if state == connectivity.Shutdown || state == connectivity.Idle {
		// Try to reconnect
		if err := conn.Connect(); err != nil {
			return nil, err
		}
	}

	return conn, nil
}

// Invoke executes a gRPC call using a pooled connection
func (p *Pool) Invoke(
	ctx context.Context,
	method string,
	args interface{},
	reply interface{},
	opts ...grpc.CallOption,
) error {
	conn, err := p.Get()
	if err != nil {
		return err
	}

	return conn.Invoke(ctx, method, args, reply, opts...)
}

// healthChecker periodically checks and reconnects unhealthy connections
func (p *Pool) healthChecker() {
	ticker := time.NewTicker(p.config.HealthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-p.ctx.Done():
			return
		case <-ticker.C:
			p.checkConnections()
		}
	}
}

// checkConnections checks all connections and reconnects if necessary
func (p *Pool) checkConnections() {
	p.mu.Lock()
	defer p.mu.Unlock()

	for i, conn := range p.conns {
		state := conn.GetState()

		switch state {
		case connectivity.Shutdown, connectivity.TransientFailure:
			// Try to reconnect
			if err := conn.Connect(); err != nil {
				// If reconnect fails, create new connection
				newConn, err := p.createConn()
				if err != nil {
					continue
				}
				p.conns[i] = newConn
			}
		}
	}
}

// Close closes all connections in the pool
func (p *Pool) Close() error {
	if p.closed.Swap(true) {
		return nil
	}

	p.cancel()

	p.mu.Lock()
	defer p.mu.Unlock()

	var lastErr error
	for _, conn := range p.conns {
		if err := conn.Close(); err != nil {
			lastErr = err
		}
	}

	p.conns = nil
	return lastErr
}

// Stats returns pool statistics
type Stats struct {
	PoolSize    int
	ActiveConns int64
	Closed      bool
}

// Stats returns current pool statistics
func (p *Pool) Stats() *Stats {
	return &Stats{
		PoolSize:    len(p.conns),
		ActiveConns: p.connCount.Load(),
		Closed:      p.closed.Load(),
	}
}

// Custom errors
var ErrPoolClosed = &PoolError{"pool is closed"}

type PoolError struct {
	msg string
}

func (e *PoolError) Error() string {
	return e.msg
}
