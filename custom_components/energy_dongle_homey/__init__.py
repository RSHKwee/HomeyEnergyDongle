"""Homey Energy Dongle integratie voor Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_IP_ADDRESS, CONF_MODE, DEFAULT_MODE, DOMAIN, PLATFORMS
from .coordinator import HomeyEnergyCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stel de integratie in vanuit een config entry."""
    ip_address = entry.data[CONF_IP_ADDRESS]
    mode = entry.data.get(CONF_MODE, DEFAULT_MODE)

    coordinator = HomeyEnergyCoordinator(hass, ip_address, mode)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Laad platforms via async_create_task zodat het BUITEN de event loop
    # wordt uitgevoerd — dit voorkomt de "blocking import_module" fout
    # die optreedt in HA 2024.7+ wanneer je direct awaitet.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS),
        eager_start=True,
    )

    # Start WebSocket listener
    await coordinator.async_start()

    logger.info(f"Homey Energy Dongle integratie gestart voor {ip_address}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder een config entry."""
    coordinator: HomeyEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Stop WebSocket listener
    await coordinator.async_stop()

    # Verwijder platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
