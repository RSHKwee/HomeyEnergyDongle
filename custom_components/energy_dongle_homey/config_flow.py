"""Config flow voor Homey Energy Dongle."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
import websockets

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_IP_ADDRESS, CONF_MODE, DEFAULT_MODE, DOMAIN

logger = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_MODE, default=DEFAULT_MODE): vol.In(["dsmr", "dlms"]),
    }
)


async def _test_connection(ip_address: str) -> str | None:
    """Test of er verbinding gemaakt kan worden. Geeft None terug bij succes, anders een foutcode."""
    uri = f"ws://{ip_address}:80/ws"
    try:
        async with asyncio.timeout(5):
            async with websockets.connect(uri) as ws:
                # Wacht op eerste bericht om te bevestigen dat er data binnenkomt
                await asyncio.wait_for(ws.recv(), timeout=4)
        return None
    except asyncio.TimeoutError:
        return "cannot_connect"
    except ConnectionRefusedError:
        return "cannot_connect"
    except Exception as e:
        logger.debug(f"Verbindingstest mislukt: {e}")
        return "cannot_connect"


class HomeyEnergyDongleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow voor Homey Energy Dongle."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Verwerk de gebruikersinvoer."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ip_address = user_input[CONF_IP_ADDRESS].strip()

            # Controleer op dubbele entries
            await self.async_set_unique_id(ip_address)
            self._abort_if_unique_id_configured()

            # Test de verbinding
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
