"""DSMR Telegram Parser for Homey Energy Dongle."""

from __future__ import annotations

import datetime
import logging
import re
from typing import Any, ClassVar

logger = logging.getLogger(__name__)

_INVALID_NO_SLASH = "Invalid telegram: missing '/'"
_INVALID_NO_EXCL = "Invalid telegram: missing '!'"
_GAS_MIN_BLOCKS = 2

TOP_LEVEL_FIELDS: frozenset[str] = frozenset(
    {
        "version",
        "version_be",
        "timestamp",
        "equipment_id",
        "electricity_tariff",
        "electricity_switch_position",
        "electricity_threshold",
        "power_failures",
        "long_power_failures",
        "fw_core_version",
    }
)


class DSMRParser:
    """Parser for DSMR P1 telegrams."""

    OBIS_CODES: ClassVar[dict[str, str]] = {
        "1-3:0.2.8": "version",
        "0-0:96.1.4": "version_be",
        "0-0:96.1.1": "equipment_id",
        "0-0:1.0.0": "timestamp",
        "1-0:1.8.1": "electricity_delivered_1",
        "1-0:1.8.2": "electricity_delivered_2",
        "1-0:2.8.1": "electricity_returned_1",
        "1-0:2.8.2": "electricity_returned_2",
        "0-0:96.14.0": "electricity_tariff",
        "0-0:96.3.10": "electricity_switch_position",
        "0-0:17.0.0": "electricity_threshold",
        "1-0:1.7.0": "power_delivered",
        "1-0:2.7.0": "power_returned",
        "1-0:21.7.0": "power_delivered_l1",
        "1-0:41.7.0": "power_delivered_l2",
        "1-0:61.7.0": "power_delivered_l3",
        "1-0:22.7.0": "power_returned_l1",
        "1-0:42.7.0": "power_returned_l2",
        "1-0:62.7.0": "power_returned_l3",
        "1-0:3.7.0": "reactive_power_delivered",
        "1-0:4.7.0": "reactive_power_returned",
        "1-0:32.7.0": "voltage_l1",
        "1-0:52.7.0": "voltage_l2",
        "1-0:72.7.0": "voltage_l3",
        "1-0:31.7.0": "current_l1",
        "1-0:51.7.0": "current_l2",
        "1-0:71.7.0": "current_l3",
        "0-0:96.7.21": "power_failures",
        "0-0:96.7.9": "long_power_failures",
        "1-0:99.97.0": "long_power_failures_log",
        "1-0:32.32.0": "voltage_sags_l1",
        "1-0:52.32.0": "voltage_sags_l2",
        "1-0:72.32.0": "voltage_sags_l3",
        "1-0:32.36.0": "voltage_swells_l1",
        "1-0:52.36.0": "voltage_swells_l2",
        "1-0:72.36.0": "voltage_swells_l3",
        "1-0:1.6.0": "max_demand_active_import",
        "0-0:98.1.0": "max_demand_last_13_months",
        "1-0:0.2.0": "fw_core_version",
        "0-1:24.2.1": "gas_delivered",
        "0-2:24.2.1": "gas_delivered_ch2",
        "0-3:24.2.1": "gas_delivered_ch3",
        "0-4:24.2.1": "gas_delivered_ch4",
        "0-1:24.1.0": "mbus_device_type1",
        "0-2:24.1.0": "mbus_device_type2",
        "0-3:24.1.0": "mbus_device_type3",
        "0-4:24.1.0": "mbus_device_type4",
    }

    def _parse_timestamp(self, ts: str) -> datetime.datetime | None:
        """Parse a DSMR timestamp string into a datetime object."""
        match = re.match(r"(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([WS])?", ts)
        if not match:
            return None
        yy, month, dd, hh, mm, ss, _ = match.groups()
        try:
            return datetime.datetime(
                2000 + int(yy),
                int(month),
                int(dd),
                int(hh),
                int(mm),
                int(ss),
                tzinfo=datetime.UTC,
            )
        except ValueError:
            return None

    def _parse_numeric_value(self, value_str: str) -> dict[str, Any]:
        """Parse a numeric value with optional unit."""
        match = re.match(r"([\d.]+)\*?(.*)", value_str.strip())
        if not match:
            try:
                return {"value": float(value_str), "unit": None}
            except ValueError:
                return {"value": value_str, "unit": None}
        value, unit = match.groups()
        try:
            return {"value": float(value), "unit": unit.strip() or None}
        except ValueError:
            return {"value": 0.0, "unit": unit.strip() or None}

    def _extract_parenthesized(self, s: str) -> list[str]:
        """Extract all (content) blocks from a string."""
        return re.findall(r"\(([^)]*)\)", s)

    def parse_line(self, line: str) -> tuple[str | None, Any]:  # noqa: PLR0911
        """Parse one line from a DSMR telegram."""
        line = line.strip().rstrip("\r\n")
        if not line:
            return None, None

        match = re.match(r"(\d+-\d+:\d+\.\d+\.\d+)(.*)", line)
        if not match:
            return None, None

        obis_code = match.group(1)
        rest = match.group(2)

        field_name = self.OBIS_CODES.get(obis_code)
        if not field_name:
            return None, None

        blocks = self._extract_parenthesized(rest)
        if not blocks:
            return None, None

        if obis_code == "0-0:1.0.0":
            return field_name, self._parse_timestamp(blocks[0])

        if field_name.startswith("gas_delivered") and len(blocks) >= _GAS_MIN_BLOCKS:
            ts = self._parse_timestamp(blocks[0])
            val = self._parse_numeric_value(blocks[1])
            return field_name, {
                "value": val["value"],
                "unit": val.get("unit", "m3"),
                "timestamp": ts,
            }

        if field_name == "long_power_failures":
            try:
                return field_name, int(blocks[0])
            except ValueError:
                return field_name, 0

        if field_name == "long_power_failures_log":
            return None, None

        value_str = blocks[0]
        if "*" in value_str:
            return field_name, self._parse_numeric_value(value_str)
        if re.match(r"^\d+$", value_str):
            return field_name, int(value_str)
        return field_name, value_str

    def parse(self, telegram: str) -> dict[str, Any]:
        """Parse a complete DSMR telegram into a structured dict."""
        telegram = telegram.strip()
        if not telegram.startswith("/"):
            raise ValueError(_INVALID_NO_SLASH)
        if "!" not in telegram:
            raise ValueError(_INVALID_NO_EXCL)

        checksum_match = re.search(r"!([A-F0-9]{4})", telegram, re.IGNORECASE)
        checksum = checksum_match.group(1) if checksum_match else ""
        data_part = telegram[: telegram.rfind("!")]

        result: dict[str, Any] = {
            "electricity": {},
            "gas": {},
            "checksum": checksum,
        }

        for line in data_part.splitlines():
            field_name, parsed_value = self.parse_line(line)
            if field_name is None or parsed_value is None:
                continue

            if field_name.startswith(("gas_delivered", "mbus_device_type")):
                key = field_name.replace("gas_delivered", "delivered")
                result["gas"][key] = parsed_value
            elif field_name in TOP_LEVEL_FIELDS:
                result[field_name] = parsed_value
            else:
                result["electricity"][field_name] = parsed_value

        return result
