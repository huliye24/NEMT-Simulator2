"""
NEMT Python Engine - gRPC Server Entry Point

This module provides a gRPC interface for the NEMT Python engine,
allowing the Electron desktop app to communicate with the engine.

Features:
- Lifecycle management (graceful shutdown)
- Electron-compatible JSON logging
- Health check endpoints
- Capsule execution
"""

import logging
import os
import signal
import sys
from concurrent import futures
from typing import Any, Dict

import grpc

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import lifecycle and logging integration
try:
    from nemt.lifecycle import get_lifecycle_manager, setup_lifecycle
    from nemt.logging_integration import setup_electron_logging
    LIFECYCLE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import lifecycle module: {e}")
    LIFECYCLE_AVAILABLE = False


class NEMTServiceServicer:
    """gRPC service implementation for NEMT engine."""

    def __init__(self):
        self.is_running = False
        logger.info("NEMTServiceServicer initialized")

    def ExecuteCapsule(self, request: Any, context: Any) -> Any:
        """Execute a capsule with given parameters."""
        try:
            capsule_name = request.capsule if hasattr(request, 'capsule') else 'unknown'
            params = request.params if hasattr(request, 'params') else {}

            logger.info(f"Executing capsule: {capsule_name}")

            # Execute the capsule
            result = self._run_capsule(capsule_name, params)

            return type('ExecuteResponse', (), {
                'result': result,
                'success': True,
                'error': ''
            })()
        except Exception as e:
            logger.error(f"Capsule execution failed: {e}")
            return type('ExecuteResponse', (), {
                'result': {},
                'success': False,
                'error': str(e)
            })()

    def GetMetrics(self, request: Any, context: Any) -> Any:
        """Get current system metrics."""
        metrics = self._collect_metrics()
        return type('MetricsResponse', (), metrics)()

    def _run_capsule(self, capsule_name: str, params: Dict) -> Dict:
        """Run a capsule (placeholder for actual implementation)."""
        logger.info(f"Running capsule: {capsule_name} with params: {params}")
        return {
            "status": "completed",
            "capsule": capsule_name,
            "output": {},
            "execution_time": 0.0
        }

    def _collect_metrics(self) -> Dict:
        """Collect system metrics."""
        import psutil
        process = psutil.Process()

        return {
            "cpu_usage": process.cpu_percent(interval=0.1),
            "memory_usage": process.memory_info().rss / (1024 * 1024),  # MB
            "threads": process.num_threads(),
            "status": "healthy" if self.is_running else "stopped"
        }


def serve(port: int = 50051):
    """Start the gRPC server."""
    logger.info(f"Starting NEMT gRPC server on port {port}...")

    # Set up lifecycle management if available
    if LIFECYCLE_AVAILABLE:
        setup_lifecycle()
        setup_electron_logging(level=logging.INFO)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )

    # Register the NEMT service
    servicer = NEMTServiceServicer()
    # Note: In production, use generated protobuf stubs:
    # nemt_pb2_grpc.add_NEMTServiceServicer_to_server(servicer, server)

    server.add_insecure_port(f'[::]:{port}')

    # Set up signal handlers (backup for non-lifecycle mode)
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}")
        if LIFECYCLE_AVAILABLE:
            lifecycle = get_lifecycle_manager()
            if not lifecycle.is_shutting_down:
                lifecycle._initiate_shutdown(f"Signal {signum}")
        else:
            logger.info("Shutting down...")
            server.stop(5)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    server.start()
    logger.info(f"NEMT gRPC server started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
        server.stop(5)

    logger.info("NEMT gRPC server stopped")


def main():
    """Main entry point."""
    port = int(os.getenv('PYTHON_GRPC_PORT', '50051'))
    logger.info("=" * 50)
    logger.info("NEMT Python Engine - gRPC Server")
    logger.info(f"Port: {port}")
    logger.info("=" * 50)

    serve(port)


if __name__ == '__main__':
    main()
