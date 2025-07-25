import time
import requests
import websockets
import asyncio
from comfydock_server.config import ServerConfig
from comfydock_server.server import ComfyDockServer


async def test_websocket(backend_url):
    """Test WebSocket connection"""
    ws_url = f"ws://{backend_url.replace('http://', '')}/ws"
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"WebSocket connected to {ws_url}")
            # Add any WebSocket test messages here if needed
            await websocket.send("test message")
            response = await websocket.recv()
            print(f"WebSocket response: {response}")
    except Exception as e:
        print(f"WebSocket test failed: {e}")


def manual_test():
    # Create test configuration
    config = ServerConfig(
        db_file_path="./environments.json",
        user_settings_file_path="./user_settings.json",
        frontend_port=8000,
        backend_port=5172,
        backend_host="127.0.0.1",
        allow_multiple_containers=False,
    )

    # Initialize server
    server = ComfyDockServer(config)

    try:
        print("Starting server...")
        server.start_backend()

        # Give server time to start
        time.sleep(2)

        # Test backend endpoint
        backend_url = f"http://{config.backend_host}:{config.backend_port}"
        print(f"Testing backend at {backend_url}")

        # Test environments endpoint
        response = requests.get(f"{backend_url}/environments")
        print(f"Environments response ({response.status_code}): {response.text}")

        # Test WebSocket connection
        asyncio.run(test_websocket(backend_url))

        # Keep server running for manual testing
        input("Press Enter to stop server...")

    finally:
        print("Stopping server...")
        server.stop()


if __name__ == "__main__":
    manual_test()
