from pydantic import BaseModel, Field, validator
from typing import List, Optional

# Pydantic configuration models
class ComfyUIVersion(BaseModel):
    """ComfyUI version configuration"""
    version: str
    git_ref: str


class TestScenario(BaseModel):
    """Test scenario configuration"""
    name: str
    description: str
    custom_nodes: List[str] = Field(default_factory=list)


class DockerConfig(BaseModel):
    """Docker configuration"""
    image: str = "comfydock-testing:latest"
    gpu_enabled: bool = True
    timeout_seconds: int = 600


class MountConfig(BaseModel):
    """Mount configuration"""
    mount_original_comfyui: bool = True
    mount_custom_nodes_only: bool = False
    mount_models: bool = True
    
    @validator('mount_custom_nodes_only')
    def validate_mount_options(cls, v, values):
        """Ensure mount options are mutually exclusive"""
        if v and values.get('mount_original_comfyui', False):
            raise ValueError("Cannot mount both original ComfyUI and custom nodes only")
        return v


class TestSettings(BaseModel):
    """Test execution settings"""
    parallel_tests: bool = False
    cleanup_on_success: bool = True
    cleanup_on_failure: bool = False
    max_retries: int = 1
    retry_delay_seconds: int = 30


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    file_path: Optional[str] = None
    
    @validator('level', 'console_level', 'file_level')
    def validate_log_level(cls, v):
        """Validate log level is valid"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


class ValidationThresholds(BaseModel):
    """Validation threshold configuration"""
    min_package_accuracy: float = 0.9
    min_import_success_rate: float = 0.8
    max_execution_time_seconds: int = 600
    
    @validator('min_package_accuracy', 'min_import_success_rate')
    def validate_percentages(cls, v):
        """Ensure percentages are between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError(f"Value must be between 0 and 1, got {v}")
        return v


class ReportingConfig(BaseModel):
    """Reporting configuration"""
    generate_html: bool = False
    generate_csv: bool = True
    generate_json: bool = True
    generate_markdown: bool = True
    upload_to_s3: bool = False


class TestSuiteInfo(BaseModel):
    """Test suite metadata"""
    name: str
    version: str


class TestSuiteConfig(BaseModel):
    """Main test suite configuration"""
    test_suite: TestSuiteInfo
    comfyui_versions: List[ComfyUIVersion]
    python_versions: List[str] = Field(default_factory=lambda: ["3.12"])
    test_scenarios: List[TestScenario]
    docker_config: DockerConfig = Field(default_factory=DockerConfig)
    mount_config: MountConfig = Field(default_factory=MountConfig)
    test_settings: TestSettings = Field(default_factory=TestSettings)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    validation_thresholds: ValidationThresholds = Field(default_factory=ValidationThresholds)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    
    @validator('python_versions')
    def validate_python_versions(cls, v):
        """Validate Python versions"""
        for version in v:
            parts = version.split('.')
            if len(parts) < 2:
                raise ValueError(f"Invalid Python version format: {version}")
            try:
                major = int(parts[0])
                minor = int(parts[1])
                if major < 3 or (major == 3 and minor < 8):
                    raise ValueError(f"Python version must be 3.8 or higher, got {version}")
            except ValueError:
                raise ValueError(f"Invalid Python version format: {version}")
        return v
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"  # Fail on unknown fields