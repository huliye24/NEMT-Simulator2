"""
NEMT Container - Electron IPC Bridge

This module enables communication between the Electron main process
and the NEMT Core Engine via stdin/stdout JSON-RPC.
"""

import json
import logging
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NEMTContainer")


@dataclass
class IPCMessage:
    """IPC Message structure"""

    request_id: str
    command: str
    args: list
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class NEMTContainerBridge:
    """
    Bridge between Electron main process and NEMT Core.
    Uses JSON-RPC over stdin/stdout for communication.
    """

    def __init__(self):
        self.handlers: dict[str, Callable] = {}
        self._running = False
        self._lock = threading.Lock()
        logger.info("NEMT Container Bridge initialized")

    def register_handler(self, command: str, handler: Callable):
        """Register a command handler"""
        with self._lock:
            self.handlers[command] = handler
        logger.info(f"Registered handler for command: {command}")

    def handle_message(self, message: IPCMessage) -> dict[str, Any]:
        """Handle an incoming IPC message"""
        command = message.command

        if command not in self.handlers:
            return {"success": False, "error": f"Unknown command: {command}", "request_id": message.request_id}

        try:
            handler = self.handlers[command]
            result = handler(*message.args)
            return {"success": True, "result": result, "request_id": message.request_id}
        except Exception as e:
            logger.exception(f"Error handling command {command}")
            return {"success": False, "error": str(e), "request_id": message.request_id}

    def send_result(self, result: dict[str, Any]):
        """Send result back to Electron main process"""
        output = json.dumps(result)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()

    def send_error(self, error: str, request_id: str):
        """Send error back to Electron main process"""
        error_msg = json.dumps({"success": False, "error": error, "request_id": request_id})
        sys.stderr.write(error_msg + "\n")
        sys.stderr.flush()

    def run(self):
        """Main loop - read commands from stdin"""
        self._running = True
        logger.info("NEMT Container Bridge running")

        while self._running:
            try:
                line = sys.stdin.readline()
                if not line:
                    # EOF - stdin closed
                    logger.info("stdin closed, exiting")
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse message
                try:
                    data = json.loads(line)
                    message = IPCMessage(
                        request_id=data.get("request_id", ""),
                        command=data.get("command", ""),
                        args=data.get("args", []),
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

                # Handle message
                result = self.handle_message(message)
                self.send_result(result)

            except Exception:
                logger.exception("Error in main loop")
                continue

    def stop(self):
        """Stop the bridge"""
        self._running = False


# Global bridge instance
_bridge: NEMTContainerBridge | None = None


def get_bridge() -> NEMTContainerBridge:
    """Get the global bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = NEMTContainerBridge()
    return _bridge


def init_container():
    """Initialize the container with command handlers"""
    from nemt.core import NEMTCore
    from nemt.data import DataFetcher
    from nemt.market import MarketAnalyzer

    bridge = get_bridge()
    core = NEMTCore()
    data_fetcher = DataFetcher()
    market_analyzer = MarketAnalyzer()

    # Register command handlers
    bridge.register_handler("ping", lambda: {"status": "ok", "time": datetime.now().isoformat()})

    bridge.register_handler("run_simulation", lambda params=None: core.run_simulation(params or {}))

    bridge.register_handler(
        "analyze_market", lambda symbol, interval, limit: market_analyzer.analyze(symbol, interval, limit)
    )

    bridge.register_handler("fetch_data", lambda symbol, interval, limit: data_fetcher.fetch(symbol, interval, limit))

    bridge.register_handler("get_status", lambda: {"running": True, "version": "1.0.0", "uptime": "N/A"})

    bridge.register_handler("get_metrics", lambda: core.get_metrics())

    logger.info("Container handlers initialized")


def run_container():
    """Run the container bridge (blocking)"""
    init_container()
    bridge = get_bridge()
    try:
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Container interrupted")
    finally:
        bridge.stop()


if __name__ == "__main__":
    run_container()
