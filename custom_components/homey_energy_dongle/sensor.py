"""Sensor platform voor Homey Energy Dongle."""

from __future__ import annotations

import logging

__all__ = ["async_setup_entry"]
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HomeyEnergyCoordinator

logger = logging.getLogger(__name__)


def _get_elec(key: str) -> Callable[[dict], Any]:
    """Helper: haal een electriciteitswaarde op uit de data."""
    def getter(data: dict) -> Any:
        value = data.get("electricity", {}).get(key)
        if isinstance(value, dict):
            return value.get("value")
        return value
    return getter


def _get_gas_delivered(data: dict) -> Any:
    """Haal gasverbruik op."""
    gas = data.get("gas", {}).get("delivered")
    if isinstance(gas, dict):
        return gas.get("value")
    return None


def _get_tariff(data: dict) -> Any:
    """Haal huidig tarief op als leesbare string."""
    tariff = data.get("electricity_tariff")
    if isinstance(tariff, dict):
        tariff = tariff.get("value")
    if tariff == 1:
        return "dal"
    if tariff == 2:
        return "piek"
    return None


@dataclass(frozen=True, kw_only=True)
class HomeyEnergySensorDescription(SensorEntityDescription):
    """Uitgebreide sensor beschrijving met data getter."""
    value_fn: Callable[[dict], Any] = lambda _: None


SENSOR_DESCRIPTIONS: tuple[HomeyEnergySensorDescription, ...] = (
    # ── Elektriciteit: verbruik ────────────────────────────────────────────
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
    # ── Elektriciteit: teruglevering ───────────────────────────────────────
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
    # ── Huidig vermogen ────────────────────────────────────────────────────
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
    # ── Spanning per fase ─────────────────────────────────────────────────
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
    # ── Stroom per fase ───────────────────────────────────────────────────
    HomeyEnergySensorDescription(
        key="current_l1",
        name="Stroom L1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("current_l1"),
    ),
    HomeyEnergySensorDescription(
        key="current_l2",
        name="Stroom L2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("current_l2"),
    ),
    HomeyEnergySensorDescription(
        key="current_l3",
        name="Stroom L3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("current_l3"),
    ),
    # ── Gas ───────────────────────────────────────────────────────────────
    HomeyEnergySensorDescription(
        key="gas_delivered",
        name="Gasverbruik",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:fire",
        value_fn=_get_gas_delivered,
    ),
    # ── Reactief vermogen ─────────────────────────────────────────────────
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
    # ── Spanningsdips per fase ────────────────────────────────────────────
    HomeyEnergySensorDescription(
        key="voltage_sags_l1",
        name="Spanningsdips L1",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_sags_l1"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_sags_l2",
        name="Spanningsdips L2",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_sags_l2"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_sags_l3",
        name="Spanningsdips L3",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_sags_l3"),
    ),
    # ── Spanningspieken per fase ──────────────────────────────────────────
    HomeyEnergySensorDescription(
        key="voltage_swells_l1",
        name="Spanningspieken L1",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert-outline",
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_swells_l1"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_swells_l2",
        name="Spanningspieken L2",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert-outline",
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_swells_l2"),
    ),
    HomeyEnergySensorDescription(
        key="voltage_swells_l3",
        name="Spanningspieken L3",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert-outline",
        entity_registry_enabled_default=False,
        value_fn=_get_elec("voltage_swells_l3"),
    ),
    # ── Storingen ─────────────────────────────────────────────────────────
    HomeyEnergySensorDescription(
        key="power_failures",
        name="Kortdurende storingen",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:power-plug-off",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("power_failures"),
    ),
    HomeyEnergySensorDescription(
        key="long_power_failures",
        name="Langdurige storingen",
        native_unit_of_measurement="count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:power-plug-off-outline",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("long_power_failures"),
    ),
    # ── Maximumtelling (Fluvius/België) ───────────────────────────────────
    HomeyEnergySensorDescription(
        key="max_demand_active_import",
        name="Vermogensvraag (huidig kwartier)",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=_get_elec("max_demand_active_import"),
    ),
    # ── Tarief ────────────────────────────────────────────────────────────
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
    """Stel sensor entities in."""
    coordinator: HomeyEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HomeyEnergySensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class HomeyEnergySensor(CoordinatorEntity[HomeyEnergyCoordinator], SensorEntity):
    """Sensor entity voor Homey Energy Dongle."""

    entity_description: HomeyEnergySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HomeyEnergyCoordinator,
        description: HomeyEnergySensorDescription,
        entry: ConfigEntry,
    ) -> None:
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
        """Geef de huidige sensorwaarde terug."""
        if not self.coordinator.data:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception as e:
            logger.debug(f"Fout bij ophalen waarde voor {self.entity_description.key}: {e}")
            return None
