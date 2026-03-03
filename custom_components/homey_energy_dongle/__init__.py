"""Homey Energy Dongle integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import CONF_IP_ADDRESS, CONF_MODE, DEFAULT_MODE, DOMAIN, PLATFORMS
from .coordinator import HomeyEnergyCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Homey Energy Dongle from a config entry."""
    ip_address: str = entry.data[CONF_IP_ADDRESS]
    mode: str = entry.data.get(CONF_MODE, DEFAULT_MODE)

    coordinator = HomeyEnergyCoordinator(hass, ip_address, mode)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS),
        eager_start=False,
    )

    await coordinator.async_start()
    logger.debug("Homey Energy Dongle started for %s", ip_address)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: HomeyEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
