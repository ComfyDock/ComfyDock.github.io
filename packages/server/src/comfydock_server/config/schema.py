import os
from pathlib import Path
from typing import Union
from pydantic import BaseModel, field_validator


class Frontend(BaseModel):
    image: str
    container_name: str
    container_port: int
    default_host_port: int


class Backend(BaseModel):
    host: str = "localhost"
    port: int = 5172


class Defaults(BaseModel):
    comfyui_path: Union[str, Path]
    db_file_path: Path
    user_settings_file_path: Path
    dockerhub_tags_url: str


class Advanced(BaseModel):
    log_level: str = "INFO"
    check_for_updates: bool = True
    update_check_interval_days: int = 1


class Logging(BaseModel):
    model_config = {'extra': 'allow'}
    
    def __init__(self, **data):
        super().__init__(**data)
        # Store all extra fields in a root dict for logging.config.dictConfig
        self.__root__ = data


class AppConfig(BaseModel):
    frontend: Frontend
    backend: Backend
    defaults: Defaults
    advanced: Advanced
    logging: Logging

    @field_validator('*', mode='before')
    @classmethod
    def expand_paths(cls, v):
        """Resolve ~ and ${ENV_VAR} → absolute paths"""
        if isinstance(v, str):
            return os.path.expandvars(os.path.expanduser(v))
        return v
    
    def update_from_dict(self, data: dict):
        """Update the config with data from a dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self