"""DataUpdateCoordinator voor Homey Energy Dongle."""

import asyncio
import logging
import websockets

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .parser import DSMRParser

logger = logging.getLogger(__name__)


class HomeyEnergyCoordinator(DataUpdateCoordinator):
    """Beheert de WebSocket verbinding en data updates."""

    def __init__(self, hass: HomeAssistant, ip_address: str, mode: str = "dsmr") -> None:
        super().__init__(
            hass,
            logger,
            name=DOMAIN,
        )
        self.ip_address = ip_address
        self.mode = mode
        self.parser = DSMRParser()
        self._ws_task: asyncio.Task | None = None
        self._running = False

    async def _async_update_data(self):
        """Data wordt via WebSocket push bijgewerkt, geen polling nodig."""
        return self.data

    async def async_start(self) -> None:
        """Start de WebSocket listener als background task."""
        self._running = True
        self._ws_task = self.hass.async_create_background_task(
            self._ws_loop(),
            "homey_energy_dongle_ws",
        )
        logger.info(f"WebSocket listener gestart voor {self.ip_address}")

    async def async_stop(self) -> None:
        """Stop de WebSocket listener."""
        self._running = False
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket listener gestopt")

    async def _ws_loop(self) -> None:
        """Hoofd WebSocket loop met automatische herverbinding."""
        uri = f"ws://{self.ip_address}:80/ws"

        while self._running:
            try:
                logger.info(f"Verbinden met {uri}...")
                async with websockets.connect(
                    uri,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                ) as websocket:
                    logger.info("WebSocket verbonden")
                    buffer = ""

                    async for message in websocket:
                        if not self._running:
                            break

                        # Decodeer bytes naar tekst indien nodig
                        if isinstance(message, bytes):
                            try:
                                text = message.decode("ascii", errors="ignore")
                            except Exception:
                                continue
                        else:
                            text = message

                        buffer += text

                        # Verwerk complete telegrams uit de buffer
                        buffer = self._process_buffer(buffer)

            except asyncio.CancelledError:
                logger.debug("WebSocket loop geannuleerd")
                break
            except websockets.exceptions.ConnectionClosed as e:
                if self._running:
                    logger.warning(f"Verbinding gesloten (code={e.code}), herverbinden in 5s...")
                    await asyncio.sleep(5)
            except ConnectionRefusedError:
                if self._running:
                    logger.error(f"Verbinding geweigerd naar {uri}, herverbinden in 10s...")
                    await asyncio.sleep(10)
            except Exception as e:
                if self._running:
                    logger.error(f"Onverwachte WebSocket fout: {e}, herverbinden in 5s...")
                    await asyncio.sleep(5)

    def _process_buffer(self, buffer: str) -> str:
        """Verwerk de buffer en extraheer complete telegrams."""
        while "/" in buffer and "!" in buffer:
            start = buffer.find("/")
            excl = buffer.find("!", start)

            if excl == -1:
                break

            # Telegram eindigt op '!' + 4 hex chars + optioneel \r\n
            # Zoek het einde inclusief eventuele newline
            tail_start = excl + 1
            tail_end = tail_start + 4

            if len(buffer) < tail_end:
                # Nog niet genoeg data ontvangen
                break

            # Controleer of de 4 tekens na '!' hex-chars zijn
            potential_checksum = buffer[tail_start:tail_end]
            if all(c in "0123456789ABCDEFabcdef" for c in potential_checksum):
                telegram = buffer[start:tail_end]
                self._handle_telegram(telegram)
                buffer = buffer[tail_end:]
                # Sla eventuele \r\n na het telegram over
                while buffer and buffer[0] in "\r\n":
                    buffer = buffer[1:]
            else:
                # Geen geldige checksum, sla dit '!' over
                buffer = buffer[excl + 1:]

        return buffer

    def _handle_telegram(self, telegram: str) -> None:
        """Verwerk een enkel telegram en update de data."""
        try:
            result = self.parser.parse(telegram)
            self.async_set_updated_data(result)
            logger.debug(
                "Telegram verwerkt: power=%.3f kW, gas=%s m³",
                result.get("electricity", {}).get("power_delivered", {}).get("value", 0)
                if isinstance(result.get("electricity", {}).get("power_delivered"), dict)
                else result.get("electricity", {}).get("power_delivered", 0),
                result.get("gas", {}).get("delivered", {}).get("value", "?")
                if isinstance(result.get("gas", {}).get("delivered"), dict)
                else "?",
            )
        except Exception as e:
            logger.warning(f"Fout bij verwerken telegram: {e}")
            logger.debug(f"Probleemtelegram: {telegram[:200]}")
