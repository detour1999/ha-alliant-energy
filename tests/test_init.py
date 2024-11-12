"""Test Alliant Energy setup."""
import pytest
from homeassistant.core import HomeAssistant
from custom_components.alliant_energy import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.alliant_energy.const import DOMAIN

@pytest.mark.asyncio
async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_data):
    """Test setting up the integration."""
    with patch(
        'custom_components.alliant_energy.client.AlliantEnergyClient.async_get_data',
        return_value=mock_data
    ):
        mock_config_entry.add_to_hass(hass)
        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

@pytest.mark.asyncio
async def test_unload_entry(hass: HomeAssistant, mock_config_entry, mock_data):
    """Test unloading the integration."""
    with patch(
        'custom_components.alliant_energy.client.AlliantEnergyClient.async_get_data',
        return_value=mock_data
    ):
        mock_config_entry.add_to_hass(hass)
        await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        assert await async_unload_entry(hass, mock_config_entry)
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]
