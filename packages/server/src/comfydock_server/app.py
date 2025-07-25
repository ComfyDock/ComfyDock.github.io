from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import AppConfig
from .routes import (
    environment_routes,
    image_routes,
    user_settings_routes,
    websocket_routes,
    comfyui_routes,
)
from comfydock_core.environment import EnvironmentManager
from comfydock_core.user_settings import UserSettingsManager
from comfydock_core.connection import ConnectionManager


def create_app(config: AppConfig) -> FastAPI:
    # Initialize core components first
    connection_manager = ConnectionManager()
    env_manager = EnvironmentManager(config.defaults.db_file_path)
    user_settings_manager = UserSettingsManager(
        config.defaults.user_settings_file_path,
        default_comfyui_path=config.defaults.comfyui_path,
    )

    # Set up WebSocket manager
    env_manager.set_ws_manager(connection_manager)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Async context manager for app lifespan management"""
        # Startup
        monitor_task = asyncio.create_task(env_manager.monitor_docker_events())

        yield  # App runs here

        # Shutdown
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

    # Create FastAPI app with lifespan
    app = FastAPI(title="ComfyDock Server", lifespan=lifespan)

    # Store managers in app state
    app.state.env_manager = env_manager
    app.state.user_settings_manager = user_settings_manager
    app.state.connection_manager = connection_manager
    app.state.config = config

    # Add routes
    app.include_router(environment_routes.router)
    app.include_router(user_settings_routes.router)
    app.include_router(image_routes.router)
    app.include_router(websocket_routes.router)
    app.include_router(comfyui_routes.router)

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
