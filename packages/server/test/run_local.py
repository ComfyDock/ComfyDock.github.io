from comfydock_server.config import load_config
from comfydock_server.server import ComfyDockServer
import logging

def run():
    
    overrides = {
        "defaults": {
            "comfyui_path": "./ComfyUI",
            "db_file_path": "./environments.json",
            "user_settings_file_path": "./user.settings.json",
        },
        "frontend": {
            "image": "akatzai/comfydock-frontend:0.2.0",
            "port": 8000,
        },
        "backend": {
            "port": 5172,
            "host": "localhost",
        },
        "advanced": {
            "log_level": "DEBUG",
            "check_for_updates": False,
            "update_check_interval_days": 0,
        },
    }

    # --------------------------------------------------------------------- #
    # 2. Load + validate final AppConfig.
    #    (You could also give user_config_path=/tmp/foo.json here.)
    # --------------------------------------------------------------------- #
    app_cfg = load_config(cli_overrides=overrides)

    # Optional: configure logging right away
    logging.config.dictConfig(app_cfg.logging.__root__)

    server = ComfyDockServer(app_cfg)

    try:
        print("Starting server...")
        server.start()

        # Keep server running for manual testing
        input("Press Enter to stop server...")

    finally:
        print("Stopping server...")
        server.stop()


if __name__ == "__main__":
    run()
