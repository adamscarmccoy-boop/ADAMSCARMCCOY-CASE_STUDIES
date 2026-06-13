import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class ProductionEngineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SESSION_INTEL_", extra="ignore")

    # Path Resolution Boundaries
    project_root: Path = Path(os.getcwd())
    parquet_lakehouse_dir: Path = Path(os.getcwd()) / "lakehouse_data"
    lancedb_uri: Path = Path(os.getcwd()) / ".vector_cache"
    
    # Engine Settings
    environment_stage: Literal["development", "production"] = "production"
    omp_num_threads: int = 4
    model_choice: str = "phi3"

    def __init__(self, **values):
        super().__init__(**values)
        self.parquet_lakehouse_dir.mkdir(parents=True, exist_ok=True)

settings = ProductionEngineSettings()
