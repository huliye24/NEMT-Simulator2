# NEMT Gateway

High-performance Go gateway for NEMT Quant Trading Platform.

## Architecture

```
Web/Electron (TypeScript) → NEMT Gateway (Go) → Python Engine
```

## Quick Start

```bash
# Install dependencies
make deps

# Build
make build

# Run
make run

# Or run directly
go run ./cmd/gateway
```

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /ready` - Readiness check

### Strategies
- `GET /api/v1/strategies` - List strategies
- `GET /api/v1/strategies/:id` - Get strategy
- `POST /api/v1/strategies` - Create strategy
- `PUT /api/v1/strategies/:id` - Update strategy
- `DELETE /api/v1/strategies/:id` - Delete strategy

### Capsules
- `GET /api/v1/capsules` - List capsules
- `GET /api/v1/capsules/:id` - Get capsule
- `POST /api/v1/capsules` - Register capsule

### Backtest
- `POST /api/v1/backtest` - Start backtest
- `GET /api/v1/backtest/:id` - Get backtest result

### Market Data
- `GET /api/v1/market/:symbol` - Get market data

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_PORT` | 8080 | HTTP server port |
| `GRPC_PORT` | 9090 | gRPC server port |
| `LOG_LEVEL` | info | Logging level |
| `LOG_FORMAT` | json | Log format (json/text) |
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `PYTHON_ENDPOINT` | localhost:50051 | Python gRPC endpoint |

## Development

```bash
# Format code
make fmt

# Run tests
make test

# Run linter
make lint

# Generate protobuf
make proto
```

## Project Structure

```
nemt-go/
├── cmd/               # Command entry points
│   ├── gateway/       # HTTP/gRPC gateway
│   ├── collector/    # Data collector
│   └── scheduler/    # Task scheduler
├── pkg/               # Public packages
│   ├── config/       # Configuration
│   ├── logger/       # Logging
│   ├── common/       # Common utilities
│   ├── models/      # Data models
│   ├── gateway/      # HTTP handlers
│   ├── middleware/   # HTTP middleware
│   └── proto/        # Protobuf generated code
├── proto/            # Protobuf definitions
└── Makefile
```

## License

MIT
