# Homey Energy Dongle — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/RSHKwee/HomeyEnergyDongle.svg)](https://github.com/RSHKwee/HomeyEnergyDongle/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration for the **Homey Energy Dongle** (P1 DSMR smart meter interface) by Athom. Data is received in real time via WebSocket push — no polling.

[![Validate with hassfest](https://github.com/RSHKwee/HomeyEnergyDongle/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/weltmeyer/ha_sonnenbatterie/actions/workflows/hassfest.yaml)
[![Validate with HACS](https://github.com/RSHKwee/HomeyEnergyDongle/actions/workflows/validate.yaml/badge.svg)](https://github.com/weltmeyer/ha_sonnenbatterie/actions/workflows/validate.yaml)


## Features

- Real-time electricity consumption and feed-in
- Gas consumption
- Power per phase (L1/L2/L3)
- Current per phase (L1/L2/L3)
- Current tariff (off-peak / peak)
- Voltage sags and swells per phase
- Short and long power failures
- Reactive power (where supported by meter)
- Peak demand / quarter-hour demand (Fluvius/Belgium)
- Automatic reconnection on connection loss

## Sensors

| Sensor | Unit | Enabled by default |
|---|---|:---:|
| Consumption off-peak | kWh | ✅ |
| Consumption peak | kWh | ✅ |
| Feed-in off-peak | kWh | ✅ |
| Feed-in peak | kWh | ✅ |
| Current consumption | kW | ✅ |
| Current feed-in | kW | ✅ |
| Power phase 1 / 2 / 3 | kW | ✅ |
| Current L1 / L2 / L3 | A | ✅ |
| Gas consumption | m³ | ✅ |
| Current tariff | off-peak/peak | ✅ |
| Voltage L1 / L2 / L3 | V | ❌ |
| Feed-in phase 1 / 2 / 3 | kW | ❌ |
| Voltage sags L1 / L2 / L3 | — | ❌ |
| Voltage swells L1 / L2 / L3 | — | ❌ |
| Short power failures | — | ❌ |
| Long power failures | — | ❌ |
| Reactive power import / export | kvar | ❌ |
| Peak demand (Fluvius) | kW | ❌ |

> **Note:** Voltage sensors are hidden by default because not all meters transmit voltage data. Enable them via **Settings → Devices & Services → Homey Energy Dongle → entities**.

## Requirements

- Home Assistant 2024.1.0 or newer
- Homey Energy Dongle reachable on your local network
- Python package: `websockets >= 11.0` (installed automatically)

## Installation via HACS

1. Go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/RSHKwee/HomeyEnergyDongle` as an **Integration**
3. Install **Homey Energy Dongle**
4. Restart Home Assistant
5. Go to **Settings → Integrations → + Add integration**
6. Search for **Homey Energy Dongle** and enter the IP address of your dongle

## Manual installation

1. Copy the `custom_components/homey_energy_dongle/` folder to your HA config directory
2. Restart Home Assistant
3. Configure via **Settings → Integrations → + Add integration**

## Tested with

| Meter | DSMR version |
|---|---|
| Landis+Gyr E350 (XMX5LGBBFFB) | 4.2 |

Should work with any DSMR 4.x / 5.x meter connected via the Homey Energy Dongle.

## Troubleshooting

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.homey_energy_dongle: debug
```

Then check **Settings → System → Logs** and filter on `HomeyEnergy`.

## License

MIT License — see [LICENSE](LICENSE) for details.
