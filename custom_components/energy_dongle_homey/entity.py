"""Base entity voor homey_energy_dongle."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import HomeyEnergyCoordinator
from .const import DOMAIN


class HomeyEnergyEntity(CoordinatorEntity[HomeyEnergyCoordinator]):
    """Basis entity class."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: HomeyEnergyCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.ip_address)},
            "name": "Homey Energy Dongle",
            "manufacturer": "Athom",
            "model": "Energy Dongle",
        }