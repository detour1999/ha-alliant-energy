# tests/conftest.py
"""Global fixtures for alliant_energy integration."""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
# Change this import
from homeassistant.helpers.entity_registry import RegistryEntryDisabler
from homeassistant.testing_config import MockConfigEntry

from custom_components.alliant_energy.const import DOMAIN
from custom_components.alliant_energy.client import AlliantEnergyClient, AlliantEnergyData

pytest_plugins = "pytest_homeassistant_custom_component"

@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "test_user",
            "password": "test_pass",
        },
        entry_id="test",
    )

@pytest.fixture
def mock_client():
    """Create a mock client."""
    with patch('aiohttp.ClientSession') as mock_session:
        client = AlliantEnergyClient("test_user", "test_pass")
        client._session = mock_session
        yield client

@pytest.fixture
def mock_data():
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
