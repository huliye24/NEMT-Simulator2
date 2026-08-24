# NEMT Gateway Makefile
# Build, test, and development tools

.PHONY: all build run test clean proto install deps fmt lint vet

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOTEST=$(GOCMD) test
GOCLEAN=$(GOCMD) clean
GOGET=$(GOCMD) get
GOMOD=$(GOCMD) mod
GOFMT=gofmt

# Binary names
BINARY_GATEWAY=nemt-gateway
BINARY_COLLECTOR=nemt-collector
BINARY_SCHEDULER=nemt-scheduler

# Build directories
BUILD_DIR=./build
DIST_DIR=./dist

# Proto files
PROTO_DIR=./proto
PROTO_OUT=./pkg/proto

# Build flags
LDFLAGS=-ldflags "-s -w"

all: clean deps fmt vet test build

# Build all binaries
build: build-gateway

build-gateway:
	@echo "Building NEMT Gateway..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_GATEWAY) ./cmd/gateway

build-collector:
	@echo "Building NEMT Collector..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_COLLECTOR) ./cmd/collector

build-scheduler:
	@echo "Building NEMT Scheduler..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_SCHEDULER) ./cmd/scheduler

# Run commands
run: run-gateway

run-gateway:
	@echo "Running NEMT Gateway..."
	$(GOCMD) run ./cmd/gateway

run-collector:
	@echo "Running NEMT Collector..."
	$(GOCMD) run ./cmd/collector

# Test commands
test:
	@echo "Running tests..."
	$(GOTEST) -v -race -cover ./...

test-coverage:
	@echo "Running tests with coverage..."
	$(GOTEST) -v -race -coverprofile=coverage.out ./...
	$(GOCMD) tool cover -html=coverage.out -o coverage.html

# Development commands
fmt:
	@echo "Formatting code..."
	$(GOFMT) -s -w .

vet:
	@echo "Running go vet..."
	$(GOCMD) vet ./...

lint:
	@echo "Running linter..."
	@which golangci-lint > /dev/null || (echo "Installing golangci-lint..." && go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest)
	golangci-lint run ./...

# Dependency management
deps:
	@echo "Downloading dependencies..."
	$(GOMOD) download
	$(GOMOD) tidy

install:
	@echo "Installing dependencies..."
	$(GOMOD) mod download

# Proto generation
proto:
	@echo "Generating protobuf code..."
	@which protoc > /dev/null || (echo "protoc not found, please install protobuf compiler" && exit 1)
	protoc --go_out=. --go_opt=paths=source_relative \
		--go-grpc_out=. --go-grpc_opt=paths=source_relative \
		$(PROTO_DIR)/*.proto

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t nemt-gateway:latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8080:8080 -p 9090:9090 nemt-gateway:latest

# Clean
clean:
	@echo "Cleaning..."
	$(GOCLEAN)
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -f coverage.out coverage.html

# Help
help:
	@echo "NEMT Gateway Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make build        Build all binaries"
	@echo "  make run          Run the gateway"
	@echo "  make test         Run tests"
	@echo "  make clean        Clean build artifacts"
	@echo "  make deps         Download dependencies"
	@echo "  make proto        Generate protobuf code"
	@echo "  make docker-build Build Docker image"
	@echo ""
