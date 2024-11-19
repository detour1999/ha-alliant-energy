"""Global fixtures for alliant_energy integration."""
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.alliant_energy.const import DOMAIN
from custom_components.alliant_energy.client import AlliantEnergyClient, AlliantEnergyData

pytest_plugins = "pytest_homeassistant_custom_component"

@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test",
        data={
            "username": "test_user",
            "password": "test_pass",
        },
        source="user",
        options={},
        unique_id="test",
        discovery_keys=["test_discovery_key"],
        entry_id="test"
    )

@pytest.fixture
def mock_data() -> AlliantEnergyData:
    """Create mock energy data."""
    data = AlliantEnergyData()
    data.usage_to_date = 500.5
    data.forecasted_usage = 750.2
    data.typical_usage = 600.0
    data.cost_to_date = 75.50
    data.forecasted_cost = 112.80
    data.typical_cost = 90.00
    data.cost_per_kwh = 0.15
    data.start_date = datetime.now() - timedelta(days=15)
    data.end_date = datetime.now() + timedelta(days=15)
    data.last_api_update = datetime.now()
    data.last_meter_read = datetime.now() - timedelta(days=1)
    return data
