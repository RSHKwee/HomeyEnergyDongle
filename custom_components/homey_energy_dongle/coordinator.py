"""DataUpdateCoordinator voor Homey Energy Dongle."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .parser import DSMRParser

logger = logging.getLogger(__name__)


class HomeyEnergyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Beheert de WebSocket verbinding en data updates."""

    def __init__(self, hass: HomeAssistant, ip_address: str, mode: str = "dsmr") -> None:
        """Initialiseer de coordinator."""
        super().__init__(hass, logger, name=DOMAIN)
        self.ip_address: str = ip_address
        self.mode: str = mode
        self.parser: DSMRParser = DSMRParser()
        self._ws_task: asyncio.Task[None] | None = None
        self._running: bool = False

    async def _async_update_data(self) -> dict[str, Any] | None:
        """Geen polling — data komt via WebSocket push."""
        return self.data

    async def async_start(self) -> None:
        """Start de WebSocket listener als HA background task."""
        self._running = True
        self._ws_task = self.hass.async_create_background_task(
            self._ws_loop(),
            "homey_energy_dongle_ws",
        )
        logger.debug("WebSocket task gestart voor %s", self.ip_address)

    async def async_stop(self) -> None:
        """Stop de WebSocket listener."""
        self._running = False
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        logger.debug("WebSocket task gestopt")

    async def _ws_loop(self) -> None:
        """Hoofd WebSocket loop met automatische herverbinding."""
        uri = f"ws://{self.ip_address}:80/ws"

        while self._running:
            try:
                logger.debug("Verbinden met %s", uri)
                async with websockets.connect(
                    uri,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                ) as websocket:
                    logger.info("Verbonden met %s", uri)
                    buffer = ""
                    async for message in websocket:
                        if not self._running:
                            break
                        text = (
                            message.decode("ascii", errors="ignore")
                            if isinstance(message, bytes)
                            else message
                        )
                        buffer += text
                        buffer = self._process_buffer(buffer)

            except asyncio.CancelledError:
                logger.debug("WebSocket loop geannuleerd")
                break
            except ConnectionClosed as err:
                if self._running:
                    logger.info("Verbinding gesloten (%s), herverbinden in 5s...", err)
                    await asyncio.sleep(5)
            except ConnectionRefusedError:
                if self._running:
                    logger.error("Verbinding geweigerd naar %s, herverbinden in 10s...", uri)
                    await asyncio.sleep(10)
            except Exception as err:  # noqa: BLE001
                if self._running:
                    logger.error("Onverwachte fout: %s, herverbinden in 5s...", err)
                    await asyncio.sleep(5)

    def _process_buffer(self, buffer: str) -> str:
        """Verwerk de buffer en extraheer complete DSMR telegrams."""
        while "/" in buffer and "!" in buffer:
            start = buffer.find("/")
            excl = buffer.find("!", start)
            if excl == -1:
                break

            tail_end = excl + 5
            if len(buffer) < tail_end:
                break

            potential_checksum = buffer[excl + 1 : tail_end]
            if all(c in "0123456789ABCDEFabcdef" for c in potential_checksum):
                telegram = buffer[start:tail_end]
                self._handle_telegram(telegram)
                buffer = buffer[tail_end:].lstrip("\r\n")
            else:
                buffer = buffer[excl + 1 :]

        return buffer

    def _handle_telegram(self, telegram: str) -> None:
        """Verwerk een enkel telegram en update coordinator data."""
        try:
            result = self.parser.parse(telegram)
            self.async_set_updated_data(result)
            logger.debug(
                "Telegram verwerkt: tariff=%s power=%s gas=%s",
                result.get("electricity_tariff"),
                result.get("electricity", {}).get("power_delivered"),
                result.get("gas", {}).get("delivered", {}).get("value")
                if isinstance(result.get("gas", {}).get("delivered"), dict)
                else None,
            )
        except Exception as err:  # noqa: BLE001
            logger.error("Fout bij verwerken telegram: %s", err)
