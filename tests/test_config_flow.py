"""Test the Alliant Energy config flow."""
import pytest
from unittest.mock import patch
from homeassistant import config_entries, data_entry_flow
from custom_components.alliant_energy import config_flow
from custom_components.alliant_energy.const import DOMAIN
from custom_components.alliant_energy.client import AlliantEnergyAuthError

@pytest.mark.asyncio
async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] is None

@pytest.mark.asyncio
async def test_valid_credentials(hass, mock_data):
    """Test that valid credentials work."""
    with patch(
        'custom_components.alliant_energy.client.AlliantEnergyClient.async_get_data',
        return_value=mock_data
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test_user",
                "password": "test_pass",
            },
        )

        assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result2["title"] == "Alliant Energy (test_user)"
        assert result2["data"] == {
            "username": "test_user",
            "password": "test_pass",
        }

@pytest.mark.asyncio
async def test_invalid_auth(hass):
    """Test invalid auth is handled."""
    with patch(
        'custom_components.alliant_energy.client.AlliantEnergyClient.async_get_data',
        side_effect=AlliantEnergyAuthError
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "invalid_user",
                "password": "invalid_pass",
            },
        )

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["errors"] == {"base": "invalid_auth"}
