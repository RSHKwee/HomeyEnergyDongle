"""Config flow for Homey Energy Dongle."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
import websockets
from homeassistant import config_entries

from .const import CONF_IP_ADDRESS, CONF_MODE, DEFAULT_MODE, DOMAIN

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

logger = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_MODE, default=DEFAULT_MODE): vol.In(["dsmr", "dlms"]),
    }
)


async def _test_connection(ip_address: str) -> str | None:
    """Test the WebSocket connection. Returns None on success, error code otherwise."""
    uri = f"ws://{ip_address}:80/ws"
    try:
        async with asyncio.timeout(5):
            async with websockets.connect(uri) as ws:
                await asyncio.wait_for(ws.recv(), timeout=4)
    except Exception:  # noqa: BLE001
        return "cannot_connect"
    else:
        return None


class HomeyEnergyDongleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Homey Energy Dongle."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ip_address: str = user_input[CONF_IP_ADDRESS].strip()

            await self.async_set_unique_id(ip_address)
            self._abort_if_unique_id_configured()

            error_code = await _test_connection(ip_address)
            if error_code:
                errors["base"] = error_code
            else:
                return self.async_create_entry(
                    title=f"Homey Energy Dongle ({ip_address})",
                    data={
                        CONF_IP_ADDRESS: ip_address,
                        CONF_MODE: user_input.get(CONF_MODE, DEFAULT_MODE),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
