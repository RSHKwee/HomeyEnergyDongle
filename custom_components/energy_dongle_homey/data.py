"""Custom types for homey_energy_dongle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from .coordinator import HomeyEnergyCoordinator


type HomeyEnergyConfigEntry = ConfigEntry[HomeyEnergyData]


@dataclass
class HomeyEnergyData:
    """Data for the Homey Energy Dongle integration."""
    coordinator: HomeyEnergyCoordinator