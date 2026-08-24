"""
NEMT Python Engine - Lifecycle Manager

Handles process lifecycle events:
- Graceful shutdown on SIGTERM/SIGINT
- State persistence before exit
- Resource cleanup
- Health check endpoint
"""

import atexit
import logging
import signal
import sys
import os
from typing import Optional

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manages the lifecycle of the NEMT Python engine process.
    
    Responsibilities:
    - Register signal handlers for graceful shutdown
    - Persist state before exit
    - Clean up resources
    - Coordinate with parent Electron process
    """

    def __init__(self):
        self.is_shutting_down = False
        self.state_persister: Optional['StatePersister'] = None
        self._setup_signal_handlers()
        self._register_atexit()

    def _setup_signal_handlers(self):
        """Register handlers for termination signals."""
        signal.signal(signal.SIGTERM, self._handle_terminate)
        signal.signal(signal.SIGINT, self._handle_interrupt)
        logger.info("Signal handlers registered")

    def _register_atexit(self):
        """Register cleanup function to run at exit."""
        atexit.register(self._cleanup)

    def _handle_terminate(self, signum, frame):
        """Handle SIGTERM signal (from parent process)."""
        logger.info(f"Received SIGTERM (signal {signum})")
        self._initiate_shutdown("SIGTERM")

    def _handle_interrupt(self, signum, frame):
        """Handle SIGINT signal (Ctrl+C)."""
        logger.info(f"Received SIGINT (signal {signum})")
        self._initiate_shutdown("SIGINT")

    def _initiate_shutdown(self, reason: str):
        """Initiate graceful shutdown sequence."""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return

        self.is_shutting_down = True
        logger.info(f"Initiating graceful shutdown: {reason}")

        try:
            # Phase 1: Stop accepting new requests
            self._stop_accepting_requests()
            
            # Phase 2: Save current state
            self._persist_state()
            
            # Phase 3: Close connections
            self._close_connections()
            
            # Phase 4: Final cleanup
            self._final_cleanup()

            logger.info("Graceful shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            sys.exit(0)

    def _stop_accepting_requests(self):
        """Stop accepting new requests."""
        logger.info("Stopping request acceptance...")
        # In a full implementation, this would:
        # - Close the gRPC server's listening port
        # - Wait for in-flight requests to complete
        # - Set a flag to reject new connections
        pass

    def _persist_state(self):
        """Persist current state before exit."""
        logger.info("Persisting state...")
        if self.state_persister:
            try:
                self.state_persister.save()
                logger.info("State persisted successfully")
            except Exception as e:
                logger.error(f"Failed to persist state: {e}")
        else:
            logger.info("No state persister configured, skipping")

    def _close_connections(self):
        """Close all open connections."""
        logger.info("Closing connections...")
        # In a full implementation, this would:
        # - Close database connections
        # - Close Redis connections
        # - Close file handles
        pass

    def _final_cleanup(self):
        """Perform final cleanup tasks."""
        logger.info("Performing final cleanup...")
        # In a full implementation, this would:
        # - Release shared memory
        # - Remove temporary files
        # - Log final statistics
        pass

    def _cleanup(self):
        """Atexit cleanup function (fallback)."""
        if not self.is_shutting_down:
            logger.info("Atexit cleanup called")
            self._persist_state()
            self._close_connections()

    def set_state_persister(self, persister: 'StatePersister'):
        """Set the state persister for shutdown."""
        self.state_persister = persister


class StatePersister:
    """Interface for persisting state."""

    def save(self):
        """Save current state to persistent storage."""
        raise NotImplementedError


class JSONStatePersister(StatePersister):
    """JSON file-based state persister."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    def save(self):
        """Save state to JSON file."""
        import json
        import tempfile

        # In a full implementation, this would:
        # - Collect current state from various components
        # - Serialize to JSON
        # - Write atomically to file

        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            dir=os.path.dirname(self.filepath),
            delete=False
        )

        try:
            state = {
                "timestamp": os.environ.get("CURRENT_TIME", ""),
                "version": "1.0",
                # Add actual state data here
            }
            json.dump(state, temp_file)
            temp_file.close()

            # Atomic rename
            os.replace(temp_file.name, self.filepath)
            logger.info(f"State saved to {self.filepath}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise


# Global lifecycle manager instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get or create the global lifecycle manager."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager


def setup_lifecycle():
    """Initialize the lifecycle manager."""
    manager = get_lifecycle_manager()
    logger.info("Lifecycle manager initialized")
    return manager
