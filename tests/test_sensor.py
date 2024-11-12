"""Test the Alliant Energy sensor platform."""
import pytest
from homeassistant.core import HomeAssistant
from custom_components.alliant_energy.sensor import async_setup_entry
from custom_components.alliant_energy.const import DOMAIN

@pytest.mark.asyncio
async def test_sensors(hass: HomeAssistant, mock_config_entry, mock_data):
    """Test sensor creation and updates."""
    with patch(
        'custom_components.alliant_energy.client.AlliantEnergyClient.async_get_data',
        return_value=mock_data
    ):
        mock_config_entry.add_to_hass(hass)
        await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        # Test basic sensor states
        state = hass.states.get("sensor.current_bill_electric_usage_to_date")
        assert state
        assert state.state == "500.5"

        state = hass.states.get("sensor.current_bill_electric_cost_to_date")
        assert state
        assert state.state == "75.50"

        state = hass.states.get("sensor.electric_cost_per_kwh")
        assert state
        assert state.state == "0.15"
        assert state.attributes["customer_charge_per_day"] == 0.4932
