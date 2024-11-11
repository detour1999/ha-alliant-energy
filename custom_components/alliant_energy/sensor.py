"""Support for Alliant Energy sensors."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util.dt import as_local

from .const import DOMAIN, ELEC_SENSORS, UPDATE_INTERVAL
from .client import AlliantEnergyClient, AlliantEnergyData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Alliant Energy sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    store = data["store"]

    client = AlliantEnergyClient(
        username=entry.data["username"],
        password=entry.data["password"],
        store=store,
    )

    async def async_update_data() -> AlliantEnergyData:
        """Fetch data from API endpoint."""
        return await client.async_get_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities = [
        AlliantEnergySensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            description=description,
        )
        for description in ELEC_SENSORS
    ]

    async_add_entities(entities)

class AlliantEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of an Alliant Energy sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
        description: AlliantEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Alliant Energy",
            "manufacturer": "Alliant Energy",
            "model": "Usage Monitor",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}

        # Add last update times if available
        if self.coordinator.data.last_api_update:
            attributes["last_api_update"] = as_local(self.coordinator.data.last_api_update).isoformat()

        if self.coordinator.data.last_meter_read:
            attributes["last_meter_read"] = as_local(self.coordinator.data.last_meter_read).isoformat()

        # Add billing period dates if available
        if self.coordinator.data.start_date:
            attributes["billing_period_start"] = as_local(self.coordinator.data.start_date).isoformat()

        if self.coordinator.data.end_date:
            attributes["billing_period_end"] = as_local(self.coordinator.data.end_date).isoformat()

        # For cost sensors, add estimated flag if applicable
        if self.entity_description.key in ["elec_cost_to_date", "elec_forecasted_cost"]:
            attributes["is_estimated"] = self.coordinator.data.is_cost_estimated

        # For cost per kWh sensor, add calculation period and customer charge
        if self.entity_description.key == "elec_cost_per_kwh":
            if self.coordinator.data.last_meter_read:
                three_months_ago = self.coordinator.data.last_meter_read - timedelta(days=90)
                attributes["calculation_period_start"] = as_local(three_months_ago).isoformat()
                attributes["calculation_period_end"] = as_local(self.coordinator.data.last_meter_read).isoformat()
            attributes["customer_charge_per_day"] = self.coordinator.data.customer_charge

        return attributes
