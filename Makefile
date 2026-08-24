# NEMT Simulator - Build System
# Unified Makefile for all platforms

.PHONY: all build dev clean test package help

# Default target
all: build

# Build all components
build: build-web build-desktop build-gateway
	@echo "Build complete!"

# Build Web frontend
build-web:
	@echo "Building Web frontend..."
	cd src/web && npm run build
	@echo "Web frontend built"

# Build Electron desktop app
build-desktop:
	@echo "Building Electron desktop app..."
	cd src/desktop && npm install
	npx tsc -p src/desktop/tsconfig.json
	@echo "Desktop app built"

# Build Go Gateway
build-gateway:
	@echo "Building Go Gateway..."
	cd src/gateway && go build -o ../../dist/gateway ./cmd/gateway
	@echo "Gateway built"

# Build Go Collector
build-collector:
	@echo "Building Go Collector..."
	cd src/collector && go build -o ../../dist/collector ./cmd/collector
	@echo "Collector built"

# Build Go Scheduler
build-scheduler:
	@echo "Building Go Scheduler..."
	cd src/scheduler && go build -o ../../dist/scheduler ./cmd/scheduler
	@echo "Scheduler built"

# Development mode
dev:
	@echo "Starting development mode..."
	npm run dev

# Package for distribution
package: build
	@echo "Packaging for distribution..."
	cd src/web && npm run build
	npx tsc -p src/desktop/tsconfig.json
	electron-builder

package:win: build
	@echo "Packaging for Windows..."
	electron-builder --win

package:mac: build
	@echo "Packaging for macOS..."
	electron-builder --mac

package:linux: build
	@echo "Packaging for Linux..."
	electron-builder --linux

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/
	rm -rf release/
	rm -rf src/web/dist
	rm -rf src/desktop/dist
	@echo "Clean complete!"

# Test
test: test-web test-go test-python

test-web:
	@echo "Testing Web frontend..."
	cd src/web && npm test || true

test-go:
	@echo "Testing Go services..."
	cd src/gateway && go test ./... || true

test-python:
	@echo "Testing Python engine..."
	cd src/nemt-os && pytest || true

# Lint
lint: lint-web lint-go

lint-web:
	@echo "Linting Web code..."
	cd src/web && npm run lint || true

lint-go:
	@echo "Linting Go code..."
	cd src/gateway && go fmt ./... && golangci-lint run || true

# Install dependencies
install: install-web install-go install-python

install-web:
	@echo "Installing Web dependencies..."
	cd src/web && npm install

install-go:
	@echo "Installing Go dependencies..."
	cd src/gateway && go mod download
	cd src/collector && go mod download
	cd src/scheduler && go mod download

install-python:
	@echo "Installing Python dependencies..."
	cd src/nemt-os && pip install -r requirements.txt || true

# Help
help:
	@echo "NEMT Simulator - Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  all              - Build all components (default)"
	@echo "  build            - Build all components"
	@echo "  build-web        - Build Web frontend only"
	@echo "  build-desktop    - Build Electron desktop app only"
	@echo "  build-gateway    - Build Go Gateway only"
	@echo "  dev              - Start development mode"
	@echo "  package          - Package for distribution"
	@echo "  package:win      - Package for Windows"
	@echo "  package:mac      - Package for macOS"
	@echo "  package:linux    - Package for Linux"
	@echo "  clean            - Remove build artifacts"
	@echo "  test             - Run all tests"
	@echo "  lint             - Run linters"
	@echo "  install          - Install all dependencies"
	@echo "  help             - Show this help"
