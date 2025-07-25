from pathlib import Path
import subprocess
import signal
import sys
from typing import Optional
from .docker_utils import DockerManager
from .config import AppConfig
import uvicorn
import threading
from .app import create_app
import logging

logger = logging.getLogger(__name__)


class ComfyDockServer:
    def __init__(self, config: AppConfig):
        self.config = config
        self.server = None
        self.server_thread = None
        self.docker = DockerManager(config)
        self.running = False
        logger.debug("ComfyDockServer initialized with config: %s", config)

    def start(self):
        """Start both backend server and frontend container"""
        logger.info("Starting ComfyDockServer...")
        self.docker.start_frontend()
        logger.info("Frontend container started")
        self.start_backend()
        self.running = True
        self._register_signal_handlers()
        logger.info("ComfyDockServer startup complete")

    def stop(self):
        """Stop both components"""
        logger.info("Stopping ComfyDockServer...")
        self.stop_backend()
        try:
            self.docker.stop_frontend()
        except Exception as e:
            logger.warning("Error stopping frontend container: %s", e)
        self.running = False
        logger.info("ComfyDockServer stopped")

    def start_backend(self):
        """Start the FastAPI server using uvicorn programmatically"""
        logger.info("Starting backend server on %s:%s", self.config.backend.host, self.config.backend.port)
        config = uvicorn.Config(
            app=create_app(self.config),
            host=self.config.backend.host,
            port=self.config.backend.port,
            log_config=None
        )
        self.server = uvicorn.Server(config)
        
        # Run server in a separate thread since server.run() is blocking
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.start()
        logger.info("Backend server thread started")

    def stop_backend(self):
        """Stop the backend server"""
        if self.server:
            logger.info("Stopping backend server...")
            self.server.should_exit = True
            if self.server_thread:
                self.server_thread.join()
                logger.info("Backend server thread stopped")

    def _register_signal_handlers(self):
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        logger.info("Registering signal handlers")
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Signal handler for shutdown"""
        logger.info("Received shutdown signal %s", signum)
        self.stop()
        sys.exit(0)