"""Binary sensor platform for homey_energy_dongle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from .data import HomeyEnergyConfigEntry

from .coordinator import HomeyEnergyCoordinator
from .const import DOMAIN

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="connected",
        name="Verbinding",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HomeyEnergyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        HomeyEnergyBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=desc,
        )
        for desc in ENTITY_DESCRIPTIONS
    )


class HomeyEnergyBinarySensor(CoordinatorEntity[HomeyEnergyCoordinator], BinarySensorEntity):
    """Toont of de WebSocket verbinding actief is."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entity_description):
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.ip_address}_connected"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.ip_address)},
        }

    @property
    def is_on(self) -> bool:
        """Geeft True als er recentelijk data is ontvangen."""
        return self.coordinator.data is not None