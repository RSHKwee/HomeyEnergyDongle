"""DSMR Telegram Parser voor Homey Energy Dongle."""

import re
import datetime
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DSMRParser:
    """Verbeterde DSMR Parser met bugfixes."""

    def __init__(self):
        self.OBIS_CODES = {
            # Identificatie & versie
            '1-3:0.2.8': 'version',
            '0-0:96.1.4': 'version_be',               # Belgische meters
            '0-0:96.1.1': 'equipment_id',
            '0-0:1.0.0': 'timestamp',

            # Electriciteit: verbruik (kWh)
            '1-0:1.8.1': 'electricity_delivered_1',
            '1-0:1.8.2': 'electricity_delivered_2',

            # Electriciteit: teruglevering (kWh)
            '1-0:2.8.1': 'electricity_returned_1',
            '1-0:2.8.2': 'electricity_returned_2',

            # Tarief
            '0-0:96.14.0': 'electricity_tariff',

            # Actueel vermogen (kW)
            '1-0:1.7.0': 'power_delivered',
            '1-0:2.7.0': 'power_returned',

            # Reactief / schijnbaar vermogen (kvar / kVA)
            '1-0:3.7.0': 'reactive_power_delivered',
            '1-0:4.7.0': 'reactive_power_returned',

            # Spanning per fase (V)
            '1-0:32.7.0': 'voltage_l1',
            '1-0:52.7.0': 'voltage_l2',
            '1-0:72.7.0': 'voltage_l3',

            # Stroom per fase (A)
            '1-0:31.7.0': 'current_l1',
            '1-0:51.7.0': 'current_l2',
            '1-0:71.7.0': 'current_l3',

            # Storingen
            '0-0:96.7.21': 'power_failures',
            '0-0:96.7.9': 'long_power_failures',

            # Spanningsdips (aantal) per fase
            '1-0:32.32.0': 'voltage_sags_l1',
            '1-0:52.32.0': 'voltage_sags_l2',
            '1-0:72.32.0': 'voltage_sags_l3',

            # Spanningspieken (aantal) per fase
            '1-0:32.36.0': 'voltage_swells_l1',
            '1-0:52.36.0': 'voltage_swells_l2',
            '1-0:72.36.0': 'voltage_swells_l3',

            # Drempelwaarde & schakelstand
            '0-0:17.0.0': 'electricity_threshold',
            '0-0:96.3.10': 'electricity_switch_position',

            # Vermogensvraag (maximumtelling, Fluvius/België)
            '1-0:1.6.0': 'max_demand_active_import',
            '0-0:98.1.0': 'max_demand_last_13_months',

            # Firmware versie
            '1-0:0.2.0': 'fw_core_version',

            # Gas (MBus kanalen 1–4)
            '0-1:24.2.1': 'gas_delivered',
            '0-2:24.2.1': 'gas_delivered_ch2',
            '0-3:24.2.1': 'gas_delivered_ch3',
            '0-4:24.2.1': 'gas_delivered_ch4',

            # MBus apparaattype (water, warmte, etc.)
            '0-1:24.1.0': 'mbus_device_type1',
            '0-2:24.1.0': 'mbus_device_type2',
            '0-3:24.1.0': 'mbus_device_type3',
            '0-4:24.1.0': 'mbus_device_type4',
        }

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime.datetime]:
        """Parse DSMR timestamp."""
        pattern = r'(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([WS])?'
        match = re.match(pattern, timestamp_str)

        if not match:
            return None

        yy, MM, dd, hh, mm, ss, dst = match.groups()
        year = 2000 + int(yy)

        try:
            return datetime.datetime(year, int(MM), int(dd), int(hh), int(mm), int(ss))
        except ValueError:
            return None

    def _parse_numeric_value(self, value_str: str) -> Dict:
        """Parse numerieke waarde met eenheid."""
        pattern = r'([\d.]+)\*?([^$]*)'
        match = re.match(pattern, value_str)

        if not match:
            try:
                return {'value': float(value_str), 'unit': None}
            except ValueError:
                return {'value': value_str, 'unit': None}

        value, unit = match.groups()
        unit = unit.strip()

        try:
            if '.' in value:
                num_value = float(value)
            else:
                num_value = float(int(value)) if value.isdigit() else float(value)
        except ValueError:
            num_value = 0.0

        return {'value': num_value, 'unit': unit}

    def _parse_gas_value(self, value_str: str) -> Dict:
        """Parse gas waarde (timestamp + waarde)."""
        try:
            if value_str.startswith('(') and value_str.endswith(')'):
                value_str = value_str[1:-1]

            if ')(' in value_str:
                timestamp_part, value_part = value_str.split(')(')
                timestamp_part = timestamp_part.strip('(')
                value_part = value_part.strip(')')

                timestamp = self._parse_timestamp(timestamp_part)
                value_info = self._parse_numeric_value(value_part)

                return {
                    'value': value_info['value'],
                    'unit': value_info.get('unit', 'm3'),
                    'timestamp': timestamp,
                    'raw_timestamp': timestamp_part,
                    'raw_value': value_part,
                }
            else:
                value_info = self._parse_numeric_value(value_str)
                return {
                    'value': value_info['value'],
                    'unit': value_info.get('unit', 'm3'),
                    'timestamp': None,
                    'raw_value': value_str,
                }

        except Exception as e:
            logger.error(f"Fout bij parsen gas waarde '{value_str}': {e}")
            return {
                'value': 0.0,
                'unit': 'm3',
                'timestamp': None,
                'error': str(e),
                'raw': value_str,
            }

    def parse_line(self, line: str) -> Tuple[Optional[str], Optional[Any]]:
        """Parse een enkele regel uit het telegram."""
        line = line.strip()
        if not line:
            return None, None

        obis_pattern = r'(\d+-\d+:\d+\.\d+\.\d+)\((.*)\)'
        match = re.match(obis_pattern, line)

        if not match:
            return None, None

        obis_code = match.group(1)
        value_str = match.group(2)

        if obis_code not in self.OBIS_CODES:
            field_name = f"unknown_{obis_code.replace(':', '_').replace('.', '_')}"
        else:
            field_name = self.OBIS_CODES[obis_code]

        if obis_code in ['0-0:1.0.0', '0-0:96.2.1']:
            parsed_value = self._parse_timestamp(value_str)
        elif obis_code in ['0-1:24.2.1', '0-2:24.2.1', '0-3:24.2.1']:
            parsed_value = self._parse_gas_value(value_str)
        elif '*' in value_str:
            parsed_value = self._parse_numeric_value(value_str)
        elif re.match(r'^\d+$', value_str):
            try:
                parsed_value = int(value_str)
            except ValueError:
                parsed_value = value_str
        elif re.match(r'^[0-9A-F]+$', value_str, re.IGNORECASE):
            parsed_value = value_str
        else:
            parsed_value = value_str

        return field_name, parsed_value

    def parse(self, telegram: str) -> Dict:
        """Parse een compleet DSMR telegram."""
        telegram = telegram.strip()

        if not telegram.startswith('/'):
            raise ValueError("Ongeldig telegram: moet beginnen met '/'")

        if '!' not in telegram:
            raise ValueError("Ongeldig telegram: mist '!' terminator")

        checksum_match = re.search(r'!([A-F0-9]{4})$', telegram)
        if not checksum_match:
            raise ValueError("Kan checksum niet vinden")

        checksum = checksum_match.group(1)
        data_part = telegram[:telegram.rfind('!')]

        result = {
            'version': None,
            'timestamp': None,
            'equipment_id': None,
            'electricity': {},
            'gas': {},
            'raw': telegram,
            'checksum': checksum,
        }

        for line in data_part.split('\n'):
            line = line.strip()
            if not line:
                continue

            field_name, parsed_value = self.parse_line(line)

            if field_name and parsed_value is not None:
                if field_name.startswith('gas_delivered'):
                    # gas_delivered → 'delivered', gas_delivered_ch2 → 'delivered_ch2'
                    key = field_name.replace('gas_delivered', 'delivered')
                    result['gas'][key] = parsed_value
                elif field_name.startswith('mbus_device_type'):
                    result['gas'][field_name] = parsed_value
                elif (
                    field_name.startswith('electricity_')
                    or field_name.startswith('power_')
                    or field_name.startswith('reactive_power_')
                    or field_name.startswith('voltage_')
                    or field_name.startswith('current_')
                    or field_name.startswith('max_demand')
                ):
                    result['electricity'][field_name] = parsed_value
                elif field_name in [
                    'version', 'version_be', 'timestamp', 'equipment_id',
                    'electricity_tariff', 'power_failures', 'long_power_failures',
                    'fw_core_version',
                ]:
                    result[field_name] = parsed_value

        return result
