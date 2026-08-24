// Package grpcserver provides gRPC server implementation
package grpcserver

import (
	"context"
	"net"
	"time"

	"github.com/nemt-lab/nemt-go/pkg/logger"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/reflection"
)

// Server represents a gRPC server
type Server struct {
	server   *grpc.Server
	listener net.Listener
	address  string
	log      *logger.Logger
}

// NewServer creates a new gRPC server
func NewServer(address string, log *logger.Logger) *Server {
	return &Server{
		address: address,
		log:     log,
	}
}

// Start starts the gRPC server
func (s *Server) Start() error {
	lis, err := net.Listen("tcp", s.address)
	if err != nil {
		return err
	}
	s.listener = lis

	// Create gRPC server with options
	s.server = grpc.NewServer(
		grpc.UnaryInterceptor(s.unaryInterceptor),
		grpc.StreamInterceptor(s.streamInterceptor),
	)

	// Register reflection service for debugging
	reflection.Register(s.server)

	s.log.Info("gRPC server starting", map[string]interface{}{
		"address": s.address,
	})

	return s.server.Serve(lis)
}

// Stop stops the gRPC server
func (s *Server) Stop() {
	if s.server != nil {
		s.log.Info("Stopping gRPC server")
		s.server.GracefulStop()
	}
}

// unaryInterceptor logs unary RPC calls
func (s *Server) unaryInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	start := time.Now()

	// Process request
	resp, err := handler(ctx, req)

	// Log request
	duration := time.Since(start)
	s.log.Info("gRPC unary call", map[string]interface{}{
		"method":   info.FullMethod,
		"duration": duration.String(),
		"error":    err,
	})

	return resp, err
}

// streamInterceptor logs streaming RPC calls
func (s *Server) streamInterceptor(
	srv interface{},
	ss grpc.ServerStream,
	info *grpc.StreamServerInfo,
	handler grpc.StreamHandler,
) error {
	start := time.Now()

	// Process stream
	err := handler(srv, ss)

	// Log stream
	duration := time.Since(start)
	s.log.Info("gRPC stream call", map[string]interface{}{
		"method":   info.FullMethod,
		"duration": duration.String(),
		"error":    err,
	})

	return err
}

// ============================================================================
// Service Implementation (Placeholder)
// ============================================================================

// NEMTGatewayService implements the generated gRPC service
type NEMTGatewayService struct {
	log *logger.Logger
}

// NewNEMTGatewayService creates a new service instance
func NewNEMTGatewayService(log *logger.Logger) *NEMTGatewayService {
	return &NEMTGatewayService{log: log}
}

// TODO: Implement all gRPC methods from proto/nemt.proto
// These will be auto-generated when we run protoc

/*
Example implementation:

func (s *NEMTGatewayService) CreateStrategy(ctx context.Context, req *proto.CreateStrategyRequest) (*proto.CreateStrategyResponse, error) {
	s.log.Info("Creating strategy via gRPC", map[string]interface{}{
		"name": req.Name,
		"type": req.Type.String(),
	})

	return &proto.CreateStrategyResponse{
		Success: true,
		Strategy: &proto.Strategy{
			Id:        uuid.New().String(),
			Name:      req.Name,
			Author:    req.Author,
			Type:      req.Type,
			Status:    proto.StrategyStatus_DRAFT,
			CreatedAt: timestamp.Now(),
		},
	}, nil
}

func (s *NEMTGatewayService) StartBacktest(req *proto.BacktestRequest, stream proto.NEMTGateway_StartBacktestServer) error {
	s.log.Info("Starting backtest via gRPC", map[string]interface{}{
		"strategy_id": req.StrategyId,
		"symbol":      req.Symbol,
	})

	// Stream results
	for i := 0; i < 100; i++ {
		select {
		case <-stream.Context().Done():
			return stream.Context().Err()
		default:
			err := stream.Send(&proto.BacktestResult{
				BarIndex:   int32(i),
				Equity:     10000 + float64(i)*100,
				Position:   0.5,
				PnL:        float64(i) * 10,
				Drawdown:   0.0,
			})
			if err != nil {
				return err
			}
			time.Sleep(100 * time.Millisecond)
		}
	}

	return nil
}
*/

// Helper function for creating insecure credentials
func GetInsecureCredentials() grpc.ServerOption {
	return grpc.Creds(insecure.NewCredentials())
}
