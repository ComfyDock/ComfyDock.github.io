"""ComfyUI models configuration loader."""
import json
from pathlib import Path

# Load configuration from JSON file
_config_path = Path(__file__).parent / "comfyui_models.json"
with open(_config_path, 'r', encoding='utf-8') as f:
    COMFYUI_MODELS_CONFIG = json.load(f)