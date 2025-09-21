from dataclasses import dataclass

@dataclass
class ModelDirectory:
    path: str
    added_at: str
    last_sync: str
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            path=data["path"],
            added_at=data["added_at"],
            last_sync=data["last_sync"],
        )
    
    @classmethod
    def to_dict(cls, instance):
        return instance.__dict__

@dataclass
class WorkspaceConfig:
    version: int
    active_environment: str
    created_at: str
    global_model_directory: ModelDirectory | None
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            version=data["version"],
            active_environment=data["active_environment"],
            created_at=data["created_at"],
            global_model_directory=ModelDirectory.from_dict(data["global_model_directory"]) if data["global_model_directory"] else data["global_model_directory"],
        )
    
    @classmethod
    def to_dict(cls, instance):
        # Need to also convert ModelDirectory
        if instance.global_model_directory:
            instance.global_model_directory = ModelDirectory.to_dict(instance.global_model_directory)
        return instance.__dict__