# Raising an Issue

Before opening an issue, please search [existing issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues) to check if it has already been reported.

When opening a new issue, include the information below. Issues missing key details may be closed without investigation.

---

## 1. Integration Version

The version number shown in **Settings → Devices & Services → Growatt Modbus → ⋮ → Integration manifest**, or the `version` field in `manifest.json`.

---

## 2. Inverter Model and Profile

- Your inverter model (e.g. `SPH 6000TL BL-UP`, `MIN 6000TL-X`, `WIT 10000TL3-X`)
- The profile selected in the integration — check **Settings → Devices & Services → Growatt Modbus → Configure**
- Single-phase or three-phase?
- Does your inverter have a battery? If so, what model?

---

## 3. Connection Type

- TCP (via Shine WiFi-X, ShineLink, or a serial-to-TCP adapter)?
- Direct serial/RTU?
- If using an adapter, what model (e.g. USR-DR164, Waveshare, EW11)?

---

## 4. What Happened vs. What You Expected

- What were you doing when the issue occurred?
- What did you expect to happen?
- What actually happened?

If entities are missing or showing wrong values, a screenshot of the affected device card in Home Assistant is very helpful.

---

## 5. Home Assistant Logs

Enable debug logging by adding the following to your `configuration.yaml`, then **restart Home Assistant** and reproduce the issue:

```yaml
logger:
  default: warning
  logs:
    custom_components.growatt_modbus: debug
```

Then copy the relevant log lines from **Settings → System → Logs** and paste them into the issue.

---

## 6. Register Scan (if relevant)

For issues with missing sensors or incorrect values, use the [Universal Register Scanner](diagnostic-service.md) to scan the relevant register range and paste the output into the issue. This is often the fastest way to diagnose a register mapping problem.
