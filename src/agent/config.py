from pathlib import Path

import yaml
from pydantic import BaseModel


class DataSource(BaseModel):
    name: str
    type: str
    path: str
    description: str


class BusinessConfig(BaseModel):
    business_id: str
    name: str
    system_prompt: str
    data_sources: list[DataSource]


CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs"


def load_business_config(business_id: str) -> BusinessConfig:
    config_path = CONFIGS_DIR / f"{business_id}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return BusinessConfig(**data)
