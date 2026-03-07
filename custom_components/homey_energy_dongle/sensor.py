"""Sensor platform for Homey Energy Dongle."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfVolume,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HomeyEnergyCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

logger = logging.getLogger(__name__)
_TARIFF_DAL = 1
_TARIFF_PIEK = 2


def _get_elec(key: str) -> Callable[[dict[str, Any]], Any]:
    """Return a getter for an electricity value."""

    def getter(data: dict[str, Any]) -> Any:
        value = data.get("electricity", {}).get(key)
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("value")
        if isinstance(value, (int, float)):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    return getter


def _get_gas_delivered(data: dict[str, Any]) -> float | None:
    """Return total gas consumption."""
    gas = data.get("gas", {}).get("delivered")
    if isinstance(gas, dict):
        return gas.get("value")
    return None


def _get_tariff(data: dict[str, Any]) -> str | None:
    """Return current tariff as a human-readable string."""
    tariff = data.get("electricity_tariff")
    if isinstance(tariff, dict):
        tariff = tariff.get("value")
    try:
        tariff = int(tariff)
    except (TypeError, ValueError):
        return None
    if tariff == _TARIFF_DAL:
        return "dal"
    if tariff == _TARIFF_PIEK:
        return "piek"
    return None


@dataclass(frozen=True, kw_only=True)
class HomeyEnergySensorDescription(SensorEntityDescription):
    """Sensor description with data getter function."""

    value_fn: Callable[[dict[str, Any]], Any] = lambda _: None


SENSOR_DESCRIPTIONS: tuple[HomeyEnergySensorDescription, ...] = (
    HomeyEnergySensorDescription(
        key="electricity_delivered_1",
        name="Verbruik dal",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-import",
        value_fn=_get_elec("electricity_delivered_1"),
    ),
    HomeyEnergySensorDescription(
        key="electricity_delivered_2",
        name="Verbruik piek",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-import",
        value_fn=_get_elec("electricity_delivered_2"),
    ),
    HomeyEnergySensorDescription(
        key="electricity_returned_1",
        name="Teruglevering dal",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-export",
        value_fn=_get_elec("electricity_returned_1"),
    ),
    HomeyEnergySensorDescription(
        key="electricity_returned_2",
        name="Teruglevering piek",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-export",
        value_fn=_get_elec("electricity_returned_2"),
    ),
    HomeyEnergySensorDescription(
        key="power_delivered",
        name="Huidig verbruik",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        value_fn=_get_elec("power_delivered"),
    ),
    HomeyEnergySensorDescription(
        key="power_returned",
        name="Huidige teruglevering",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=_get_elec("power_returned"),
    ),
    HomeyEnergySensorDescription(
        key="power_delivered_l1",
        name="Vermogen (fase 1)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("power_delivered_l1"),
    ),
    HomeyEnergySensorDescription(
        key="power_delivered_l2",
        name="Vermogen (fase 2)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("power_delivered_l2"),
    ),
    HomeyEnergySensorDescription(
        key="power_delivered_l3",
        name="Vermogen (fase 3)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("power_delivered_l3"),
    ),
    HomeyEnergySensorDescription(
        key="power_returned_l1",
        name="Teruglevering (fase 1)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("power_returned_l1"),
    ),
    HomeyEnergySensorDescription(
        key="power_returned_l2",
        name="Teruglevering (fase 2)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("power_returned_l2"),
    ),
    HomeyEnergySensorDescription(
        key="power_returned_l3",
        name="Teruglevering (fase 3)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("power_returned_l3"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_l1",
        name="Spanning L1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_l1"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_l2",
        name="Spanning L2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_l2"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_l3",
        name="Spanning L3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_l3"),
    ),
    HomeyEnergySensorDescription(
        key="current_l1",
        name="Stroom L1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("current_l1"),
    ),
    HomeyEnergySensorDescription(
        key="current_l2",
        name="Stroom L2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("current_l2"),
    ),
    HomeyEnergySensorDescription(
        key="current_l3",
        name="Stroom L3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_elec("current_l3"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_sags_l1",
        name="Spanningsdips L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
        value_fn=_get_elec("voltage_sags_l1"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_sags_l2",
        name="Spanningsdips L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
        value_fn=_get_elec("voltage_sags_l2"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_sags_l3",
        name="Spanningsdips L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
        value_fn=_get_elec("voltage_sags_l3"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_swells_l1",
        name="Spanningspieken L1",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert-outline",
        value_fn=_get_elec("voltage_swells_l1"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_swells_l2",
        name="Spanningspieken L2",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert-outline",
        value_fn=_get_elec("voltage_swells_l2"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_swells_l3",
        name="Spanningspieken L3",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert-outline",
        value_fn=_get_elec("voltage_swells_l3"),
    ),
    HomeyEnergySensorDescription(
        key="power_failures",
        name="Kortdurende storingen",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:power-plug-off",
        value_fn=lambda d: d.get("power_failures"),
    ),
    HomeyEnergySensorDescription(
        key="long_power_failures",
        name="Langdurige storingen",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:power-plug-off-outline",
        value_fn=lambda d: d.get("long_power_failures"),
    ),
    HomeyEnergySensorDescription(
        key="reactive_power_delivered",
        name="Reactief vermogen import",
        native_unit_of_measurement="kvar",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("reactive_power_delivered"),
    ),
    HomeyEnergySensorDescription(
        key="reactive_power_returned",
        name="Reactief vermogen export",
        native_unit_of_measurement="kvar",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("reactive_power_returned"),
    ),
    HomeyEnergySensorDescription(
        key="max_demand_active_import",
        name="Vermogensvraag (huidig kwartier)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("max_demand_active_import"),
    ),
    HomeyEnergySensorDescription(
        key="gas_delivered",
        name="Gasverbruik",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:fire",
        value_fn=_get_gas_delivered,
    ),
    HomeyEnergySensorDescription(
        key="electricity_tariff",
        name="Huidig tarief",
        icon="mdi:cash-clock",
        value_fn=_get_tariff,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for this config entry."""
    coordinator: HomeyEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HomeyEnergySensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class HomeyEnergySensor(CoordinatorEntity[HomeyEnergyCoordinator], SensorEntity):
    """Sensor entity for Homey Energy Dongle."""

    entity_description: HomeyEnergySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HomeyEnergyCoordinator,
        description: HomeyEnergySensorDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Homey Energy Dongle",
            "manufacturer": "Athom",
            "model": "Energy Dongle",
            "configuration_url": f"http://{coordinator.ip_address}",
        }

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        if not self.coordinator.data:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception:  # noqa: BLE001
            logger.debug("Error getting value for %s", self.entity_description.key)
            return None
