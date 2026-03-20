import pytest

from agent.config import load_business_config


def test_load_valid_config():
    config = load_business_config("acme_retail")
    assert config.business_id == "acme_retail"
    assert config.name == "Acme Retail Support"
    assert len(config.data_sources) == 2
    assert config.data_sources[0].name == "orders"
    assert config.data_sources[1].name == "products"
    assert "customer service agent" in config.system_prompt.lower()


def test_load_missing_config():
    with pytest.raises(FileNotFoundError):
        load_business_config("nonexistent_business")
