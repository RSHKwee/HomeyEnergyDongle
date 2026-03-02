# Homey Energy Dongle – Home Assistant Custom Integration

Integreert de **Homey Energy Dongle** (P1 DSMR meter) als custom component in Home Assistant via WebSocket.

## Sensoren

| Sensor | Eenheid | Omschrijving |
|---|---|---|
| Verbruik dal | kWh | Electriciteitsverbruik tarief 1 |
| Verbruik piek | kWh | Electriciteitsverbruik tarief 2 |
| Teruglevering dal | kWh | Zonnepanelen teruglevering tarief 1 |
| Teruglevering piek | kWh | Zonnepanelen teruglevering tarief 2 |
| Huidig verbruik | kW | Actueel vermogen verbruik |
| Huidige teruglevering | kW | Actueel vermogen teruglevering |
| Spanning L1/L2/L3 | V | Spanning per fase (standaard verborgen) |
| Stroom L1/L2/L3 | A | Stroom per fase (standaard verborgen) |
| Gasverbruik | m³ | Totaal gasverbruik |
| Huidig tarief | — | `dal` of `piek` |

## Installatie

### Handmatig

1. Kopieer de map `homey_energy_dongle/` naar:
   ```
   <config>/custom_components/homey_energy_dongle/
   ```
2. Herstart Home Assistant.
3. Ga naar **Instellingen → Integraties → Integratie toevoegen**.
4. Zoek op **Homey Energy Dongle**.
5. Voer het IP-adres van je dongle in.

### Via HACS (als je de repo publiceert)

1. Voeg de repository toe als custom repository in HACS.
2. Installeer de integratie via HACS.
3. Herstart Home Assistant en configureer via de UI.

## Vereisten

- Home Assistant 2023.1 of nieuwer
- Python package: `websockets>=11.0` (wordt automatisch geïnstalleerd)
- Homey Energy Dongle bereikbaar op het lokale netwerk

## Probleemoplossing

Zet logging aan in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.homey_energy_dongle: debug
```
