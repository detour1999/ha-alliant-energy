"""Test the Alliant Energy config flow."""
from unittest.mock import patch
import pytest
from homeassistant import data_entry_flow
from homeassistant.config_entries import SOURCE_USER
from custom_components.alliant_energy.const import DOMAIN
from custom_components.alliant_energy.client import AlliantEnergyAuthError

async def test_form(hass):
    """Test we get the form."""
    with patch("custom_components.alliant_energy.config_flow.ConfigFlow.async_step_user", return_value={"type": data_entry_flow.RESULT_TYPE_FORM}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}
